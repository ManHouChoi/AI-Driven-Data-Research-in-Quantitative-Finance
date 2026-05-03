# Formula Coverage Report

| Formula | Included? | Section | Appendix? | Source Logic | Verified |
|---|---:|---|---:|---|---:|
| Risk exposure vector / paragraph share normalization | Yes | Section 4, Section 5 | No | `risk_scoring.py`, annual taxonomy `risk_vectors.csv` construction | Yes |
| Feature-window definition | Yes | Section 3 | No | July-to-June feature/target alignment in GAT and portfolio code | Yes |
| Return target construction | Yes | Section 3 | No | `generate_fin_data.py` target convention summarized in report | Yes |
| Volatility target construction | Yes | Section 3 | No | Annualized realized volatility target | Yes |
| Log return | Yes | Section 3 | No | Financial feature construction | Yes |
| Realized volatility / downside volatility | Yes | Section 3 | No | Financial feature construction | Yes |
| Moving-average ratio | Yes | Section 3 | No | Feature list and report formula | Yes |
| Momentum construction | Yes | Section 3 | No | Feature list and report formula | Yes |
| Dollar volume and log dollar volume | Yes | Section 3 | No | Feature list and report formula | Yes |
| Median imputation | Yes | Section 3 | No | `FinancialGraphBuilder._fit_feature_preprocessor` | Yes |
| Feature standardization | Yes | Section 3 | No | Train-only scaler in `GAT_data_pipeline.py` | Yes |
| Text context construction | Yes | Section 4 | No | Update-pack `full_context` construction | Yes |
| Sentence embedding vector | Yes | Section 4 | No | `all-MiniLM-L6-v2` taxonomy encoder implementation | Yes |
| Cosine similarity | Yes | Section 4, Section 5 | No | Taxonomy and graph construction | Yes |
| UMAP projection | Yes | Section 4 | No | Update-pack `build_taxonomy.py` | Yes |
| HDBSCAN assignment | Yes | Section 4 | No | Update-pack `build_taxonomy.py` | Yes |
| Hybrid centroid | Yes | Section 4 | No | 0.7 data centroid + 0.3 semantic centroid in taxonomy construction logic | Yes |
| Nearest-centroid noise assignment | Yes | Section 4 | No | Update-pack noise resolution | Yes |
| Dynamic deviation indicator | Yes | Section 4 | No | Update-pack threshold `theta=0.45` | Yes |
| ADD centroid update | Yes | Section 4 | No | Update-pack `execute_add_logic` | Yes |
| MERGE centroid update | Yes | Section 4 | No | Update-pack MERGE rule | Yes |
| Expanded full-window sensitivity grid | Yes | Section 4 | No | `scripts/run_taxonomy_sensitivity.py`; supports Macro/Meso sizes, UMAP, HDBSCAN samples, centroid/merge weights, prompt size, and seeds; `theta040` executed | Yes |
| Paired Macro/Meso variant downstream improvement estimand | Yes | Section 4 and Section 7 | No | Sensitivity-to-ST-GAT bridge; default and `theta040` Macro/Meso forecast outputs regenerated or validated | Yes |
| Graph object definition | Yes | Section 5 | No | `FinancialGraphBuilder` snapshot design | Yes |
| Adjacency threshold | Yes | Section 5 | No | `FinancialGraphBuilder._build_weighted_edges` | Yes |
| Full graph vs identity baseline | Yes | Section 5 | No | Explicit self-loop graph and identity ablation | Yes |
| Graph density | Yes | Appendix A | Yes | `compute_graph_diagnostics` | Yes |
| Degree statistics | Yes | Appendix A | Yes | Graph diagnostics | Yes |
| GAT attention score | Yes | Section 5 | No | `GATConv` formulation | Yes |
| Softmax attention | Yes | Section 5 | No | GAT formulation | Yes |
| Node aggregation | Yes | Section 5 | No | GAT formulation | Yes |
| Multi-head attention | Yes | Section 5 | No | `heads` hyperparameter | Yes |
| Temporal convolution | Yes | Section 5 | No | `ST_GAT_Forecaster.tcn` | Yes |
| Output prediction layer | Yes | Section 5 and Section 9 | No | Two-output return/volatility head | Yes |
| Masked multi-task Huber loss | Yes | Section 5 | No | `masked_huber_loss` | Yes |
| Scalar Huber loss | Yes | Appendix A | Yes | Loss definition | Yes |
| Regularized objective / weight decay | Yes | Appendix A | Yes | Adam weight decay in GAT scripts | Yes |
| MSE | Yes | Appendix A | Yes | Evaluation metric | Yes |
| RMSE | Yes | Appendix A | Yes | OOS metric tables | Yes |
| MAE | Yes | Appendix A | Yes | OOS metric tables | Yes |
| Spearman rank correlation | Yes | Appendix A | Yes | `safe_spearman` in forecast scripts | Yes |
| R-squared | Yes | Appendix A | Yes | Included for completeness; not a headline metric | Yes |
| Portfolio return | Yes | Section 8, Appendix A | Yes | `portfolio_backtest.py` | Yes |
| Transaction-cost adjustment | Yes | Section 8, Appendix A | Yes | 10 bps cost + 5 bps slippage | Yes |
| Turnover | Yes | Section 8, Appendix A | Yes | One-way turnover in backtester | Yes |
| Sharpe ratio | Yes | Appendix A | Yes | Portfolio metrics | Yes |
| Sortino ratio | Yes | Appendix A | Yes | Portfolio metrics | Yes |
| Maximum drawdown | Yes | Appendix A | Yes | Portfolio metrics | Yes |
| Beta | Yes | Appendix A | Yes | Benchmark regression in backtester | Yes |
| Bootstrap confidence interval | Yes | Appendix A | Yes | `evaluate_oos_robustness.py` design | Yes |
| Newey-West/HAC adjustment | Yes | Appendix A | Yes | `evaluate_portfolio_inference.py`, FMB appendix | Yes |
| Fama-MacBeth stage 1 regression | Yes | Appendix B | Yes | `fmb_risk_premium.py` design | Yes |
| Fama-MacBeth time-series premium | Yes | Appendix B and Appendix A | Yes | FMB design | Yes |
| DAV / EGARCH-X variance equation | Yes | Appendix B | Yes | `volatility_model.py` design | Yes |
| SAR network equation | Yes | Appendix D | Yes | `network_evolution_analysis.py` design | Yes |

Result: zero required formula categories are missing from the report or appendix.
