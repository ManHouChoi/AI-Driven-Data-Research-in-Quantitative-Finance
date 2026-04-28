# generate_fin_data.py
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")


@dataclass
class WindowBounds:
    """July-to-June feature and target windows for a given risk year."""

    feat_start: pd.Timestamp
    feat_end: pd.Timestamp
    mom_end: pd.Timestamp
    target_start: pd.Timestamp
    target_end: pd.Timestamp


class FinancialDataEngineer:
    """Construct the enhanced ST-GAT financial feature matrix.

    Alignment convention:
        For risk year t, firm-level and market features are measured over
        July 1 of t through June 30 of t+1. Forward targets are measured over
        July 1 of t+1 through June 30 of t+2.

    This design is intentionally compatible with annual 10-K risk scores and
    avoids look-ahead bias for one-period-ahead forecasting.
    """

    MARKET_TICKERS: Dict[str, str] = {
        "SP500": "^GSPC",
        "VIX": "^VIX",
        "TENY": "^TNX",
    }

    MIN_FEATURE_DAYS = 100
    MIN_TARGET_DAYS = 50

    def __init__(self, risk_csv_path: str):
        self.risk_csv_path = risk_csv_path
        self.risk_df = pd.read_csv(risk_csv_path)
        self._validate_risk_df()

        self.tickers = sorted(self.risk_df["Ticker"].dropna().unique().tolist())
        self.years = sorted(self.risk_df["Year"].dropna().astype(int).unique().tolist())
        self.price_data = pd.DataFrame()
        self.volume_data = pd.DataFrame()
        self.market_price_data: Dict[str, pd.Series] = {}
        self.dropped_records: List[Dict[str, object]] = []

    def _validate_risk_df(self) -> None:
        required = {"Ticker", "Year"}
        missing = required.difference(self.risk_df.columns)
        if missing:
            raise ValueError(f"Risk CSV missing required columns: {sorted(missing)}")

        self.risk_df["Ticker"] = self.risk_df["Ticker"].astype(str).str.upper().str.strip()
        self.risk_df["Year"] = pd.to_numeric(self.risk_df["Year"], errors="coerce")
        self.risk_df = self.risk_df.dropna(subset=["Ticker", "Year"])
        self.risk_df["Year"] = self.risk_df["Year"].astype(int)

    def _date_bounds(self) -> Tuple[str, str]:
        start_year = min(self.years)
        end_year = max(self.years) + 2
        return f"{start_year}-01-01", f"{end_year}-12-31"

    @staticmethod
    def _normalise_index(df_or_series):
        if hasattr(df_or_series.index, "tz") and df_or_series.index.tz is not None:
            df_or_series.index = df_or_series.index.tz_localize(None)
        return df_or_series.sort_index()

    @staticmethod
    def _extract_field(df: pd.DataFrame, field_name: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            if field_name in df.columns.get_level_values(0):
                return df[field_name]
            return pd.DataFrame()

        if field_name in df.columns:
            return pd.DataFrame(df[field_name])
        return pd.DataFrame()

    def fetch_market_data(self) -> None:
        """Fetch firm prices, firm volumes, and market proxy series from Yahoo Finance."""
        start_date, end_date = self._date_bounds()
        print(
            f"Fetching firm market data for {len(self.tickers)} equities "
            f"from {start_date} to {end_date}..."
        )

        firm_df = yf.download(
            self.tickers,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=True,
        )

        adj_close = self._extract_field(firm_df, "Adj Close")
        close = self._extract_field(firm_df, "Close")
        volume = self._extract_field(firm_df, "Volume")

        if adj_close.empty and close.empty:
            raise ValueError("Could not fetch firm price data from Yahoo Finance.")

        self.price_data = adj_close if not adj_close.empty else close
        self.volume_data = volume

        self.price_data = self._normalise_index(self.price_data)
        if not self.volume_data.empty:
            self.volume_data = self._normalise_index(self.volume_data)

        available = set(self.price_data.columns.astype(str))
        unavailable = sorted(set(self.tickers).difference(available))
        if unavailable:
            print(f"Warning: {len(unavailable)} tickers unavailable in price data. Example: {unavailable[:10]}")

        print("Fetching market/macro proxy data: S&P 500, VIX, 10Y Treasury yield proxy...")
        for label, yahoo_ticker in self.MARKET_TICKERS.items():
            proxy_df = yf.download(
                yahoo_ticker,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                progress=False,
                threads=True,
            )
            series_df = self._extract_field(proxy_df, "Adj Close")
            if series_df.empty:
                series_df = self._extract_field(proxy_df, "Close")

            if series_df.empty:
                print(f"Warning: failed to fetch market proxy {label} ({yahoo_ticker}).")
                continue

            series = series_df.iloc[:, 0].dropna()
            self.market_price_data[label] = self._normalise_index(series)

        print("Market data fetched successfully.")

    @staticmethod
    def make_windows(year: int) -> WindowBounds:
        return WindowBounds(
            feat_start=pd.Timestamp(year=year, month=7, day=1),
            feat_end=pd.Timestamp(year=year + 1, month=6, day=30),
            mom_end=pd.Timestamp(year=year + 1, month=5, day=31),
            target_start=pd.Timestamp(year=year + 1, month=7, day=1),
            target_end=pd.Timestamp(year=year + 2, month=6, day=30),
        )

    @staticmethod
    def _log_returns(series: pd.Series) -> pd.Series:
        return np.log(series / series.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()

    @staticmethod
    def _cumulative_return(series: pd.Series) -> float:
        clean = series.dropna()
        if len(clean) < 2 or clean.iloc[0] <= 0:
            return np.nan
        return float((clean.iloc[-1] - clean.iloc[0]) / clean.iloc[0])

    @staticmethod
    def _last_available_price(series: pd.Series, end_date: pd.Timestamp) -> Optional[float]:
        hist = series.loc[:end_date].dropna()
        if hist.empty:
            return None
        return float(hist.iloc[-1])

    def _record_drop(self, ticker: str, year: int, reason: str) -> None:
        self.dropped_records.append({"Ticker": ticker, "Year": year, "Reason": reason})

    def _firm_features(self, ticker: str, year: int, series: pd.Series, volume: Optional[pd.Series]) -> Optional[Dict[str, float]]:
        windows = self.make_windows(year)
        feat_series = series.loc[windows.feat_start:windows.feat_end].dropna()
        if len(feat_series) < self.MIN_FEATURE_DAYS:
            self._record_drop(ticker, year, f"insufficient feature price days: {len(feat_series)}")
            return None

        log_returns = self._log_returns(feat_series)
        if log_returns.empty:
            self._record_drop(ticker, year, "empty feature log returns")
            return None

        vol = float(log_returns.std() * np.sqrt(252))
        downside = log_returns[log_returns < 0]
        downside_vol = float(downside.std() * np.sqrt(252)) if len(downside) >= 2 else np.nan

        ma_200 = float(feat_series.tail(200).mean())
        current_price = float(feat_series.iloc[-1])
        ma_200_ratio = (current_price / ma_200) - 1.0 if ma_200 > 0 else np.nan

        try:
            p_start = self._last_available_price(series, windows.feat_start)
            p_mom_end = self._last_available_price(series, windows.mom_end)
            momentum_11m = (p_mom_end - p_start) / p_start if p_start and p_start > 0 and p_mom_end else np.nan
        except Exception:
            momentum_11m = np.nan

        dollar_volume = np.nan
        log_dollar_volume = np.nan
        if volume is not None and not volume.empty:
            vol_series = volume.loc[windows.feat_start:windows.feat_end].dropna()
            aligned = pd.concat([feat_series.rename("price"), vol_series.rename("volume")], axis=1).dropna()
            if not aligned.empty:
                dollar_volume = float((aligned["price"] * aligned["volume"]).mean())
                log_dollar_volume = float(np.log1p(dollar_volume)) if dollar_volume >= 0 else np.nan

        target_series = series.loc[windows.target_start:windows.target_end].dropna()
        if len(target_series) < self.MIN_TARGET_DAYS:
            self._record_drop(ticker, year, f"insufficient target price days: {len(target_series)}")
            return None

        target_log_rets = self._log_returns(target_series)
        if target_log_rets.empty:
            self._record_drop(ticker, year, "empty target log returns")
            return None

        target_vol = float(target_log_rets.std() * np.sqrt(252))
        target_ret = self._cumulative_return(target_series)

        return {
            "Vol": vol,
            "Downside_Vol": downside_vol,
            "MA_200_Ratio": ma_200_ratio,
            "Momentum_11M": momentum_11m,
            "Dollar_Volume": dollar_volume,
            "Log_Dollar_Volume": log_dollar_volume,
            "Target_Ret": target_ret,
            "Target_Vol": target_vol,
        }

    def _market_features(self, year: int) -> Dict[str, float]:
        windows = self.make_windows(year)
        features = {
            "SP500_Ret": np.nan,
            "SP500_Vol": np.nan,
            "VIX_Avg": np.nan,
            "VIX_Change": np.nan,
            "TenY_Yield_Avg": np.nan,
            "TenY_Yield_Change": np.nan,
        }

        sp500 = self.market_price_data.get("SP500")
        if sp500 is not None and not sp500.empty:
            sp_window = sp500.loc[windows.feat_start:windows.feat_end].dropna()
            if len(sp_window) >= self.MIN_FEATURE_DAYS:
                features["SP500_Ret"] = self._cumulative_return(sp_window)
                sp_rets = self._log_returns(sp_window)
                features["SP500_Vol"] = float(sp_rets.std() * np.sqrt(252)) if not sp_rets.empty else np.nan

        vix = self.market_price_data.get("VIX")
        if vix is not None and not vix.empty:
            vix_window = vix.loc[windows.feat_start:windows.feat_end].dropna()
            if len(vix_window) >= 20:
                features["VIX_Avg"] = float(vix_window.mean())
                features["VIX_Change"] = self._cumulative_return(vix_window)

        teny = self.market_price_data.get("TENY")
        if teny is not None and not teny.empty:
            teny_window = teny.loc[windows.feat_start:windows.feat_end].dropna()
            if len(teny_window) >= 20:
                features["TenY_Yield_Avg"] = float(teny_window.mean() / 10.0)
                features["TenY_Yield_Change"] = float((teny_window.iloc[-1] - teny_window.iloc[0]) / 10.0)

        return features

    def build_financial_matrix(self) -> pd.DataFrame:
        """Build enhanced financial feature matrix for exact Ticker-Year risk pairs."""
        if self.price_data.empty:
            raise RuntimeError("price_data is empty. Run fetch_market_data() before build_financial_matrix().")

        print("Calculating enhanced temporal features and forward targets...")
        records = []
        valid_pairs = self.risk_df[["Ticker", "Year"]].drop_duplicates().values
        market_feature_cache = {year: self._market_features(int(year)) for year in self.years}

        for ticker, year_raw in valid_pairs:
            year = int(year_raw)
            if ticker not in self.price_data.columns:
                self._record_drop(ticker, year, "ticker not found in price matrix")
                continue

            series = self.price_data[ticker].dropna()
            if series.empty:
                self._record_drop(ticker, year, "empty ticker price series")
                continue

            volume = None
            if not self.volume_data.empty and ticker in self.volume_data.columns:
                volume = self.volume_data[ticker].dropna()

            firm_features = self._firm_features(ticker, year, series, volume)
            if firm_features is None:
                continue

            record = {
                "Year": year,
                "Ticker": ticker,
                **firm_features,
                **market_feature_cache.get(year, {}),
            }
            records.append(record)

        fin_df = pd.DataFrame(records)
        if fin_df.empty:
            raise ValueError("No valid financial records were generated.")

        fin_df = fin_df.dropna(subset=["Target_Ret", "Target_Vol"])
        fin_df = fin_df.sort_values(["Year", "Ticker"]).reset_index(drop=True)
        return fin_df

    def export_drop_log(self, output_path: str) -> None:
        if not self.dropped_records:
            return
        drop_df = pd.DataFrame(self.dropped_records)
        drop_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    PROJECT_ROOT = os.getenv("FYP_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))

    RISK_CSV = os.getenv(
        "FYP_RISK_SCORES_MACRO_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "risk_scores_macro_annual.csv"),
    )
    OUTPUT_CSV = os.getenv(
        "FYP_FIN_MATRIX_ENHANCED_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "fin_data_matrix_enhanced.csv"),
    )
    DROP_LOG_CSV = os.getenv(
        "FYP_FIN_MATRIX_DROP_LOG_CSV",
        os.path.join(PROJECT_ROOT, "data", "interim", "scoring_outputs", "fin_data_matrix_enhanced_drop_log.csv"),
    )

    if not os.path.exists(RISK_CSV):
        print(f"Error: Could not locate {RISK_CSV}")
        print("Set FYP_RISK_SCORES_MACRO_CSV or place the file under data/interim/scoring_outputs/.")
    else:
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        os.makedirs(os.path.dirname(DROP_LOG_CSV), exist_ok=True)

        engineer = FinancialDataEngineer(RISK_CSV)
        engineer.fetch_market_data()
        fin_df = engineer.build_financial_matrix()

        fin_df.to_csv(OUTPUT_CSV, index=False)
        engineer.export_drop_log(DROP_LOG_CSV)

        print(f"\nEnhanced financial matrix generated: {fin_df.shape[0]} valid temporal records.")
        print(f"Columns: {list(fin_df.columns)}")
        print(f"Exported to: {OUTPUT_CSV}")
        if engineer.dropped_records:
            print(f"Drop log exported to: {DROP_LOG_CSV}")
        print("\nPreview:")
        print(fin_df.head())
