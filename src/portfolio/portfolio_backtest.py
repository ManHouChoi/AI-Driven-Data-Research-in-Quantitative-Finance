

# GAT_portfolio_construction.py
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import yfinance as yf

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))

CONFIG = {
    # Primary signal source: use the meso topology-only ST-GAT output by default.
    "signal_csv": os.getenv(
        "FYP_GAT_MESO_PANEL_CSV",
        os.path.join(
            os.getenv("FYP_GAT_MESO_OUTPUT_DIR", os.path.join(PROJECT_ROOT, "outputs", "gat", "GAT_output_meso")),
            "ST_GAT_vs_Baseline_Panel_meso.csv",
        ),
    ),
    "output_dir": os.getenv(
        "FYP_PORTFOLIO_OUTPUT_DIR",
        os.path.join(PROJECT_ROOT, "outputs", "portfolio", "GAT_portfolio_output"),
    ),
    "benchmark_ticker": "SPY",
    "price_start": "2021-07-01",
    "price_end": "2025-07-01",
    "prediction_model_prefix": "GAT",
    "score_methods": ["return_only", "return_over_vol", "composite_z"],
    "composite_vol_penalty": 0.50,
    "rebalance_frequency": "ME",
    "top_quantile": 0.20,
    "bottom_quantile": 0.20,
    "volatility_floor": 0.10,
    "max_long_weight": 0.05,
    "transaction_cost_bps": 10.0,
    "slippage_bps": 5.0,
    "initial_capital": 1.0,
    "annualization_factor": 12,
}


@dataclass
class PortfolioBacktestResult:
    name: str
    monthly_returns: pd.Series
    monthly_turnover: pd.Series
    weights: pd.DataFrame
    metrics: Dict[str, float]


class PredictionWeightedPortfolioBacktester:
    """Monthly portfolio backtest using annual ST-GAT prediction signals.

    Signal timing convention:
        A row with Year=t in the forecast panel is assumed to predict the
        July t+1 through June t+2 holding window. The score is therefore
        persistent across the 12 monthly rebalances in that holding window.

    This avoids look-ahead bias while still allowing monthly rebalancing for
    weight drift, transaction-cost accounting, and risk control. A rebalance at
    month-end m forms target weights using information available at m, then earns
    the next month's return m+1.
    """

    def __init__(self, config: Dict[str, object]):
        self.config = config
        self.output_dir = str(config["output_dir"])
        os.makedirs(self.output_dir, exist_ok=True)

        self.signal_df = pd.DataFrame()
        self.monthly_prices = pd.DataFrame()
        self.monthly_returns = pd.DataFrame()
        self.benchmark_returns = pd.Series(dtype=float)
        self.results: Dict[str, PortfolioBacktestResult] = {}
        self.spread_diagnostics = pd.DataFrame()

    @staticmethod
    def _one_way_cost_rate(transaction_cost_bps: float, slippage_bps: float) -> float:
        return (transaction_cost_bps + slippage_bps) / 10_000.0

    @staticmethod
    def _month_end_index(start: str, end: str) -> pd.DatetimeIndex:
        return pd.date_range(start=start, end=end, freq="ME")

    @staticmethod
    def _extract_price_panel(raw_df: pd.DataFrame) -> pd.DataFrame:
        if raw_df.empty:
            raise ValueError("Yahoo Finance returned an empty price dataframe.")

        if isinstance(raw_df.columns, pd.MultiIndex):
            if "Adj Close" in raw_df.columns.get_level_values(0):
                prices = raw_df["Adj Close"]
            elif "Close" in raw_df.columns.get_level_values(0):
                prices = raw_df["Close"]
            else:
                raise ValueError("Downloaded data does not contain Adj Close or Close prices.")
        else:
            if "Adj Close" in raw_df.columns:
                prices = pd.DataFrame(raw_df["Adj Close"])
            elif "Close" in raw_df.columns:
                prices = pd.DataFrame(raw_df["Close"])
            else:
                raise ValueError("Downloaded data does not contain Adj Close or Close prices.")

        if hasattr(prices.index, "tz") and prices.index.tz is not None:
            prices.index = prices.index.tz_localize(None)
        return prices.sort_index()

    def load_signals(self) -> None:
        signal_csv = str(self.config["signal_csv"])
        if not os.path.exists(signal_csv):
            raise FileNotFoundError(
                f"Signal CSV not found: {signal_csv}. "
                "Set FYP_GAT_MESO_PANEL_CSV or run the Meso ST-GAT forecast first."
            )

        df = pd.read_csv(signal_csv)
        required = {
            "Ticker",
            "Year",
            "Dataset",
            "GAT_Pred_Ret",
            "GAT_Pred_Vol",
            "Base_Pred_Ret",
            "Base_Pred_Vol",
        }
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Signal CSV missing required columns: {sorted(missing)}")

        df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        df = df.dropna(subset=["Ticker", "Year"])
        df["Year"] = df["Year"].astype(int)

        self.signal_df = df.sort_values(["Year", "Ticker"]).reset_index(drop=True)
        print(f"Loaded {len(self.signal_df):,} prediction rows from {signal_csv}.")

    def fetch_monthly_prices(self) -> None:
        if self.signal_df.empty:
            raise RuntimeError("Signals are empty. Run load_signals() first.")

        tickers = sorted(self.signal_df["Ticker"].unique().tolist())
        benchmark = str(self.config["benchmark_ticker"])
        all_tickers = sorted(set(tickers + [benchmark]))

        start = str(self.config["price_start"])
        end = str(self.config["price_end"])
        print(f"Fetching daily prices for {len(all_tickers)} tickers from {start} to {end}...")

        raw_df = yf.download(
            all_tickers,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            threads=True,
        )
        daily_prices = self._extract_price_panel(raw_df)

        available = set(daily_prices.columns.astype(str))
        missing = sorted(set(all_tickers).difference(available))
        if missing:
            print(f"Warning: {len(missing)} tickers missing from price data. Example: {missing[:10]}")

        monthly_prices = daily_prices.resample("ME").last().dropna(axis=1, how="all")
        monthly_returns = monthly_prices.pct_change().replace([np.inf, -np.inf], np.nan)

        if benchmark not in monthly_returns.columns:
            raise ValueError(f"Benchmark ticker {benchmark} not available in downloaded price data.")

        self.benchmark_returns = monthly_returns[benchmark].dropna().rename("Benchmark")
        stock_cols = [c for c in monthly_returns.columns if c != benchmark]
        self.monthly_prices = monthly_prices[stock_cols]
        self.monthly_returns = monthly_returns[stock_cols]

        self.monthly_prices.to_csv(os.path.join(self.output_dir, "monthly_prices.csv"))
        self.monthly_returns.to_csv(os.path.join(self.output_dir, "monthly_returns.csv"))
        self.benchmark_returns.to_csv(os.path.join(self.output_dir, "benchmark_monthly_returns.csv"))
        print("Monthly price and return panels exported.")

    @staticmethod
    def signal_window(year: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """Prediction Year=t applies from July t+1 through June t+2."""
        start = pd.Timestamp(year=year + 1, month=7, day=31)
        end = pd.Timestamp(year=year + 2, month=6, day=30) + pd.offsets.MonthEnd(0)
        return start, end

    def _active_signal_for_month(self, rebalance_date: pd.Timestamp, model_prefix: str, score_method: str) -> pd.DataFrame:
        records = []
        ret_col = f"{model_prefix}_Pred_Ret"
        vol_col = f"{model_prefix}_Pred_Vol"

        if ret_col not in self.signal_df.columns or vol_col not in self.signal_df.columns:
            raise ValueError(f"Could not find prediction columns {ret_col} and {vol_col}.")

        for year, group in self.signal_df.groupby("Year"):
            start, end = self.signal_window(int(year))
            if start <= rebalance_date <= end:
                active = group[["Ticker", "Year", ret_col, vol_col]].copy()
                active = active.rename(columns={ret_col: "Pred_Ret", vol_col: "Pred_Vol"})
                records.append(active)

        if not records:
            return pd.DataFrame(columns=["Ticker", "Year", "Pred_Ret", "Pred_Vol", "Score"])

        active_df = pd.concat(records, ignore_index=True)
        active_df = active_df.dropna(subset=["Pred_Ret", "Pred_Vol"])
        active_df["Pred_Vol"] = active_df["Pred_Vol"].clip(lower=float(self.config["volatility_floor"]))
        active_df["Score"] = self._compute_score(active_df, score_method=score_method)
        return active_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["Score"])

    def _compute_score(self, signal_df: pd.DataFrame, score_method: str) -> pd.Series:
        """Convert predicted return/volatility into a portfolio-ranking score.

        Supported methods:
            return_only:     rank only by predicted return.
            return_over_vol: rank by predicted return divided by predicted volatility.
            composite_z:     z(predicted return) - lambda * z(predicted volatility).
        """
        if score_method == "return_only":
            return signal_df["Pred_Ret"].astype(float)

        if score_method == "return_over_vol":
            return signal_df["Pred_Ret"].astype(float) / signal_df["Pred_Vol"].astype(float)

        if score_method == "composite_z":
            ret = signal_df["Pred_Ret"].astype(float)
            vol = signal_df["Pred_Vol"].astype(float)
            ret_std = ret.std(ddof=0)
            vol_std = vol.std(ddof=0)
            z_ret = (ret - ret.mean()) / ret_std if ret_std > 0 else pd.Series(0.0, index=signal_df.index)
            z_vol = (vol - vol.mean()) / vol_std if vol_std > 0 else pd.Series(0.0, index=signal_df.index)
            penalty = float(self.config["composite_vol_penalty"])
            return z_ret - penalty * z_vol

        raise ValueError(f"Unsupported score_method: {score_method}")

    def _eligible_tickers(self, rebalance_date: pd.Timestamp) -> List[str]:
        if rebalance_date not in self.monthly_returns.index:
            return []
        ret_row = self.monthly_returns.loc[rebalance_date]
        return ret_row.dropna().index.astype(str).tolist()

    def _long_only_weights(self, signal_df: pd.DataFrame, eligible: List[str]) -> pd.Series:
        signal_df = signal_df[signal_df["Ticker"].isin(eligible)].copy()
        if signal_df.empty:
            return pd.Series(dtype=float)

        n_select = max(1, int(np.ceil(len(signal_df) * float(self.config["top_quantile"]))))
        selected = signal_df.nlargest(n_select, "Score").copy()

        inv_vol = 1.0 / selected["Pred_Vol"].clip(lower=float(self.config["volatility_floor"]))
        raw_weights = inv_vol / inv_vol.sum()
        weights = pd.Series(raw_weights.values, index=selected["Ticker"].values, dtype=float)

        max_w = float(self.config["max_long_weight"])
        if max_w > 0:
            weights = weights.clip(upper=max_w)
            if weights.sum() > 0:
                weights = weights / weights.sum()

        return weights.sort_index()

    def _long_short_weights(self, signal_df: pd.DataFrame, eligible: List[str]) -> pd.Series:
        signal_df = signal_df[signal_df["Ticker"].isin(eligible)].copy()
        if signal_df.empty or len(signal_df) < 2:
            return pd.Series(dtype=float)

        n_long = max(1, int(np.ceil(len(signal_df) * float(self.config["top_quantile"]))))
        n_short = max(1, int(np.ceil(len(signal_df) * float(self.config["bottom_quantile"]))))

        long_leg = signal_df.nlargest(n_long, "Score").copy()
        short_leg = signal_df.nsmallest(n_short, "Score").copy()
        overlap = set(long_leg["Ticker"]).intersection(set(short_leg["Ticker"]))
        if overlap:
            long_leg = long_leg[~long_leg["Ticker"].isin(overlap)]
            short_leg = short_leg[~short_leg["Ticker"].isin(overlap)]

        if long_leg.empty or short_leg.empty:
            return pd.Series(dtype=float)

        long_inv_vol = 1.0 / long_leg["Pred_Vol"].clip(lower=float(self.config["volatility_floor"]))
        short_inv_vol = 1.0 / short_leg["Pred_Vol"].clip(lower=float(self.config["volatility_floor"]))

        long_weights = 0.5 * long_inv_vol / long_inv_vol.sum()
        short_weights = -0.5 * short_inv_vol / short_inv_vol.sum()

        weights = pd.concat([
            pd.Series(long_weights.values, index=long_leg["Ticker"].values, dtype=float),
            pd.Series(short_weights.values, index=short_leg["Ticker"].values, dtype=float),
        ])
        return weights.groupby(level=0).sum().sort_index()

    @staticmethod
    def _align_weights(weights: pd.Series, universe: List[str]) -> pd.Series:
        return weights.reindex(universe).fillna(0.0).astype(float)

    def _run_strategy(self, name: str, portfolio_type: str, model_prefix: str, score_method: str) -> PortfolioBacktestResult:
        cost_rate = self._one_way_cost_rate(
            float(self.config["transaction_cost_bps"]),
            float(self.config["slippage_bps"]),
        )

        rebalance_dates = self.monthly_returns.index.intersection(
            self._month_end_index(str(self.config["price_start"]), str(self.config["price_end"]))
        )
        rebalance_dates = rebalance_dates.sort_values()
        # A rebalance at month-end t earns the return from t to t+1.
        tradable_return_dates = self.monthly_returns.index.sort_values()

        all_returns = []
        all_turnover = []
        weight_records = []
        prev_weights = pd.Series(dtype=float)

        for date in rebalance_dates:
            eligible = self._eligible_tickers(date)
            if not eligible:
                continue

            next_pos = tradable_return_dates.searchsorted(date, side="right")
            if next_pos >= len(tradable_return_dates):
                continue
            holding_return_date = tradable_return_dates[next_pos]

            active_signal = self._active_signal_for_month(
                date,
                model_prefix=model_prefix,
                score_method=score_method,
            )
            if active_signal.empty:
                continue

            if portfolio_type == "long_only":
                target_weights = self._long_only_weights(active_signal, eligible)
            elif portfolio_type == "long_short":
                target_weights = self._long_short_weights(active_signal, eligible)
            else:
                raise ValueError(f"Unsupported portfolio_type: {portfolio_type}")

            if target_weights.empty:
                continue

            universe = sorted(set(prev_weights.index).union(set(target_weights.index)).union(set(eligible)))
            target_weights = self._align_weights(target_weights, universe)
            prev_weights = self._align_weights(prev_weights, universe)

            turnover = float(np.abs(target_weights - prev_weights).sum())
            cost = turnover * cost_rate

            period_returns = self.monthly_returns.loc[holding_return_date].reindex(universe).fillna(0.0)
            gross_return = float((target_weights * period_returns).sum())
            net_return = gross_return - cost

            all_returns.append((holding_return_date, net_return))
            all_turnover.append((date, turnover))

            weight_row = target_weights[target_weights.abs() > 1e-12].copy()
            for ticker, weight in weight_row.items():
                weight_records.append({
                    "Rebalance_Date": date,
                    "Holding_Return_Date": holding_return_date,
                    "Ticker": ticker,
                    "Weight": weight,
                    "Score_Method": score_method,
                    "Model_Prefix": model_prefix,
                })

            # Approximate post-return drift before next rebalance.
            drifted = target_weights * (1.0 + period_returns)
            gross_exposure = float(drifted.abs().sum())
            prev_weights = drifted / gross_exposure if gross_exposure > 0 else pd.Series(dtype=float)

        monthly_ret = pd.Series(dict(all_returns), name=name).sort_index()
        monthly_turnover = pd.Series(dict(all_turnover), name=f"{name}_Turnover").sort_index()
        weights_df = pd.DataFrame(weight_records)
        metrics = self._performance_metrics(monthly_ret, monthly_turnover)

        return PortfolioBacktestResult(
            name=name,
            monthly_returns=monthly_ret,
            monthly_turnover=monthly_turnover,
            weights=weights_df,
            metrics=metrics,
        )

    def _compute_top_bottom_spread_diagnostics(self) -> pd.DataFrame:
        """Compute monthly top-minus-bottom realized return spreads by signal ranking.

        This diagnostic directly tests whether the model's cross-sectional ranking
        separates future winners from losers. For each rebalance month, the signal
        at month-end t is sorted, and the average next-month return of the top
        quantile is compared against the bottom quantile.
        """
        records = []
        tradable_return_dates = self.monthly_returns.index.sort_values()

        model_prefixes = [str(self.config["prediction_model_prefix"]), "Base"]
        model_labels = {
            str(self.config["prediction_model_prefix"]): "ST-GAT",
            "Base": "Identity Baseline",
        }

        rebalance_dates = self.monthly_returns.index.intersection(
            self._month_end_index(str(self.config["price_start"]), str(self.config["price_end"]))
        ).sort_values()

        for model_prefix in model_prefixes:
            for score_method in self.config["score_methods"]:
                monthly_spreads = []
                for date in rebalance_dates:
                    next_pos = tradable_return_dates.searchsorted(date, side="right")
                    if next_pos >= len(tradable_return_dates):
                        continue
                    holding_return_date = tradable_return_dates[next_pos]

                    eligible = self._eligible_tickers(date)
                    if not eligible:
                        continue

                    active_signal = self._active_signal_for_month(
                        date,
                        model_prefix=model_prefix,
                        score_method=score_method,
                    )
                    active_signal = active_signal[active_signal["Ticker"].isin(eligible)].copy()
                    if len(active_signal) < 2:
                        continue

                    n_top = max(1, int(np.ceil(len(active_signal) * float(self.config["top_quantile"]))))
                    n_bottom = max(1, int(np.ceil(len(active_signal) * float(self.config["bottom_quantile"]))))
                    top = active_signal.nlargest(n_top, "Score")
                    bottom = active_signal.nsmallest(n_bottom, "Score")

                    next_returns = self.monthly_returns.loc[holding_return_date]
                    top_ret = next_returns.reindex(top["Ticker"]).dropna()
                    bottom_ret = next_returns.reindex(bottom["Ticker"]).dropna()
                    if top_ret.empty or bottom_ret.empty:
                        continue

                    monthly_spreads.append({
                        "Rebalance_Date": date,
                        "Holding_Return_Date": holding_return_date,
                        "Model": model_labels.get(model_prefix, model_prefix),
                        "Model_Prefix": model_prefix,
                        "Score_Method": score_method,
                        "Top_Return": float(top_ret.mean()),
                        "Bottom_Return": float(bottom_ret.mean()),
                        "Top_Minus_Bottom": float(top_ret.mean() - bottom_ret.mean()),
                        "Num_Top": int(len(top_ret)),
                        "Num_Bottom": int(len(bottom_ret)),
                    })

                spread_df = pd.DataFrame(monthly_spreads)
                if spread_df.empty:
                    continue

                spread_series = spread_df["Top_Minus_Bottom"].dropna()
                t_stat = np.nan
                p_value = np.nan
                if len(spread_series) >= 2 and spread_series.std(ddof=1) > 0:
                    test = stats.ttest_1samp(spread_series, popmean=0.0, nan_policy="omit")
                    t_stat = float(test.statistic)
                    p_value = float(test.pvalue)

                records.append({
                    "Model": model_labels.get(model_prefix, model_prefix),
                    "Model_Prefix": model_prefix,
                    "Score_Method": score_method,
                    "Mean_Monthly_Top_Return": float(spread_df["Top_Return"].mean()),
                    "Mean_Monthly_Bottom_Return": float(spread_df["Bottom_Return"].mean()),
                    "Mean_Monthly_TopMinusBottom": float(spread_series.mean()),
                    "Annualized_TopMinusBottom": float(spread_series.mean() * float(self.config["annualization_factor"])),
                    "Spread_TStat": t_stat,
                    "Spread_PValue": p_value,
                    "Positive_Spread_Rate": float((spread_series > 0).mean()),
                    "Num_Months": int(len(spread_series)),
                })

                spread_df.to_csv(
                    os.path.join(
                        self.output_dir,
                        f"top_bottom_monthly_spreads_{model_prefix}_{score_method}.csv",
                    ),
                    index=False,
                )

        diagnostics = pd.DataFrame(records)
        if not diagnostics.empty:
            diagnostics = diagnostics.sort_values(
                by=["Annualized_TopMinusBottom", "Spread_TStat"],
                ascending=[False, False],
                na_position="last",
            )
        return diagnostics

    def _performance_metrics(self, returns: pd.Series, turnover: pd.Series) -> Dict[str, float]:
        returns = returns.dropna()
        if returns.empty:
            return {}

        ann = float(self.config["annualization_factor"])
        total_return = float((1.0 + returns).prod() - 1.0)
        n_periods = len(returns)
        annualized_return = float((1.0 + total_return) ** (ann / n_periods) - 1.0)
        annualized_vol = float(returns.std(ddof=0) * np.sqrt(ann))
        sharpe = annualized_return / annualized_vol if annualized_vol > 0 else np.nan

        downside = returns[returns < 0]
        downside_vol = float(downside.std(ddof=0) * np.sqrt(ann)) if len(downside) > 1 else np.nan
        sortino = annualized_return / downside_vol if downside_vol and downside_vol > 0 else np.nan

        equity = (1.0 + returns).cumprod()
        running_max = equity.cummax()
        drawdown = equity / running_max - 1.0
        max_drawdown = float(drawdown.min())

        hit_rate = float((returns > 0).mean())
        avg_turnover = float(turnover.reindex(returns.index).fillna(0.0).mean())

        benchmark = self.benchmark_returns.reindex(returns.index).dropna()
        aligned_returns = returns.reindex(benchmark.index).dropna()
        benchmark = benchmark.reindex(aligned_returns.index).dropna()

        alpha_ann = np.nan
        beta = np.nan
        information_ratio = np.nan
        benchmark_corr = np.nan
        if len(aligned_returns) >= 6 and len(benchmark) == len(aligned_returns):
            X = sm.add_constant(benchmark.values)
            y = aligned_returns.values
            model = sm.OLS(y, X).fit()
            alpha_monthly = float(model.params[0])
            beta = float(model.params[1])
            alpha_ann = float((1.0 + alpha_monthly) ** ann - 1.0)
            active = aligned_returns - benchmark
            tracking_error = float(active.std(ddof=0) * np.sqrt(ann))
            active_return = float(active.mean() * ann)
            information_ratio = active_return / tracking_error if tracking_error > 0 else np.nan
            benchmark_corr = float(aligned_returns.corr(benchmark))

        return {
            "Total_Return": total_return,
            "Annualized_Return": annualized_return,
            "Annualized_Volatility": annualized_vol,
            "Sharpe": sharpe,
            "Sortino": sortino,
            "Max_Drawdown": max_drawdown,
            "Hit_Rate": hit_rate,
            "Average_Monthly_Turnover": avg_turnover,
            "Alpha_Annualized_vs_Benchmark": alpha_ann,
            "Beta_vs_Benchmark": beta,
            "Information_Ratio_vs_Benchmark": information_ratio,
            "Correlation_vs_Benchmark": benchmark_corr,
            "Num_Months": float(len(returns)),
        }

    def run(self) -> None:
        self.load_signals()
        self.fetch_monthly_prices()

        primary_prefix = str(self.config["prediction_model_prefix"])
        strategies = []
        for score_method in self.config["score_methods"]:
            strategies.extend([
                (f"GAT_LongOnly_TopQuintile_{score_method}", "long_only", primary_prefix, score_method),
                (f"GAT_LongShort_TopBottomQuintile_{score_method}", "long_short", primary_prefix, score_method),
                (f"Identity_LongOnly_TopQuintile_{score_method}", "long_only", "Base", score_method),
                (f"Identity_LongShort_TopBottomQuintile_{score_method}", "long_short", "Base", score_method),
            ])

        for name, portfolio_type, prefix, score_method in strategies:
            print(f"Running strategy: {name}")
            result = self._run_strategy(
                name=name,
                portfolio_type=portfolio_type,
                model_prefix=prefix,
                score_method=score_method,
            )
            self.results[name] = result

            result.monthly_returns.to_csv(os.path.join(self.output_dir, f"returns_{name}.csv"))
            result.monthly_turnover.to_csv(os.path.join(self.output_dir, f"turnover_{name}.csv"))
            if not result.weights.empty:
                result.weights.to_csv(os.path.join(self.output_dir, f"weights_{name}.csv"), index=False)

        self.spread_diagnostics = self._compute_top_bottom_spread_diagnostics()
        if not self.spread_diagnostics.empty:
            self.spread_diagnostics.to_csv(
                os.path.join(self.output_dir, "top_bottom_spread_diagnostics.csv"),
                index=False,
            )

        self._export_summary()
        self._plot_equity_curves()
        print(f"Portfolio backtest complete. Outputs saved in: {self.output_dir}")

    def _export_summary(self) -> None:
        rows = []
        for name, result in self.results.items():
            row = {"Strategy": name, **result.metrics}
            rows.append(row)

        summary = pd.DataFrame(rows)

        benchmark = self.benchmark_returns.dropna()
        if not benchmark.empty:
            benchmark_metrics = self._performance_metrics(
                benchmark.rename("Benchmark"),
                pd.Series(0.0, index=benchmark.index),
            )
            summary = pd.concat(
                [summary, pd.DataFrame([{ "Strategy": "Benchmark_SPY", **benchmark_metrics }])],
                ignore_index=True,
            )

        summary.to_csv(os.path.join(self.output_dir, "portfolio_performance_summary.csv"), index=False)
        if not summary.empty and "Strategy" in summary.columns:
            summary_ranked = summary.sort_values(
                by=["Sharpe", "Annualized_Return"],
                ascending=[False, False],
                na_position="last",
            )
            summary_ranked.to_csv(
                os.path.join(self.output_dir, "portfolio_performance_summary_ranked.csv"),
                index=False,
            )
        if not self.spread_diagnostics.empty:
            print("\nTop-bottom spread diagnostics:")
            print(self.spread_diagnostics)
        print("\nPortfolio performance summary:")
        print(summary)

    def _plot_equity_curves(self) -> None:
        plt.figure(figsize=(12, 7))

        for name, result in self.results.items():
            if result.monthly_returns.empty:
                continue
            equity = (1.0 + result.monthly_returns).cumprod()
            plt.plot(equity.index, equity.values, label=name, linewidth=1.5, alpha=0.75)

        benchmark = self.benchmark_returns.dropna()
        if not benchmark.empty:
            bench_equity = (1.0 + benchmark).cumprod()
            plt.plot(bench_equity.index, bench_equity.values, label="Benchmark_SPY", linestyle="--", linewidth=2)

        plt.title("ST-GAT Prediction-Weighted Portfolio Backtest")
        plt.xlabel("Date")
        plt.ylabel("Growth of $1")
        plt.legend(fontsize=9)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "portfolio_equity_curves.png"), dpi=300)
        plt.close()


if __name__ == "__main__":
    backtester = PredictionWeightedPortfolioBacktester(CONFIG)
    backtester.run()
