import pandas as pd
import torch
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_prediction_vs_price(model, val_dataset, valid_tickers, price_data):
    """
    Selects the ticker with the highest predicted crash risk and plots
    the probability against the actual price trajectory.
    """
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # 1. Generate all predictions for the validation set
    all_probs = []
    with torch.no_grad():
        for i in range(len(val_dataset)):
            x, mask, f, _ = val_dataset[i]
            # Add batch dimension and move to device
            logits = model(x.unsqueeze(0).to(device),
                           mask.unsqueeze(0).to(device),
                           f.unsqueeze(0).to(device))
            all_probs.append(torch.sigmoid(logits).item())

    # 2. Identify a "Success Case" (High predicted risk + actual crash)
    # Or just the highest risk ticker to see what the model "saw"
    val_tickers = valid_tickers[len(valid_tickers) - len(val_dataset):] # Align tickers
    results_df = pd.DataFrame({'Ticker': val_tickers, 'Prob': all_probs})
    target_ticker = results_df.sort_values(by='Prob', ascending=False).iloc[0]['Ticker']
    predicted_risk = results_df.sort_values(by='Prob', ascending=False).iloc[0]['Prob']

    print(f"Plotting Case Study: {target_ticker} (Predicted Crash Prob: {predicted_risk:.2%})")

    # 3. Extract Price Data (2023-2024)
    ticker_px = price_data[target_ticker].loc['2023-01-01':'2024-12-31']
    cum_return = (ticker_px / ticker_px.iloc[0]) - 1

    # 4. Generate the Visualization
    fig, ax1 = plt.subplots(figsize=(12, 6))
    sns.set_theme(style="white")

    # Plot Actual Returns
    ax1.plot(cum_return.index, cum_return.values, color='royalblue', lw=2, label='Actual Cumulative Return')
    ax1.set_ylabel('Cumulative Return (%)', fontsize=12, fontweight='bold', color='royalblue')
    ax1.axhline(y=-0.15, color='red', linestyle='--', alpha=0.6, label='Crash Threshold (-15%)')
    ax1.tick_params(axis='y', labelcolor='royalblue')

    # Add a secondary axis for the Model Prediction
    ax2 = ax1.twinx()
    # We plot the prediction as a constant "Signal" for the forward-looking year
    # since 10-K is annual, the risk is 'broadcast' across the period
    ax2.fill_between(cum_return.index, 0, predicted_risk, color='orange', alpha=0.2, label='Model Predicted Risk')
    ax2.set_ylabel('Transformer Crash Probability', fontsize=12, fontweight='bold', color='darkorange')
    ax2.set_ylim(0, 1)
    ax2.tick_params(axis='y', labelcolor='darkorange')

    plt.title(f"Transformer Case Study: {target_ticker} (2023-2024)", fontsize=16, fontweight='bold')
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.85))

    output_path = "transformer_case_study.png"
    plt.savefig(output_path, dpi=300)
    print(f"Visualization saved to {output_path}")
    plt.show()

# To run this, call it after your optimize_architecture loop:
# best_model = study.best_trial... (instantiate with best params)
# plot_prediction_vs_price(best_model, val_dataset, unique_tickers, engine.price_data)