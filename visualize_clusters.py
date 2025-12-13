import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.preprocessing import MinMaxScaler
import os

INPUT_FILE = "wallet_dataset_labeled.csv"
OUTPUT_DIR = "docs"
RADAR_CHART_FILE = os.path.join(OUTPUT_DIR, "persona_radar_chart.png")
TSNE_PLOT_FILE = os.path.join(OUTPUT_DIR, "clusters_tsne.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return None
    return pd.read_csv(INPUT_FILE)

def plot_radar_chart(df):
    print("Generating Radar Chart")
    
    features = [
        'tx_count', 'active_days', 'total_gas_spent', 
        'total_nft_volume_usd', 'dex_trades', 'total_traded_usd'
    ]
    
    scaler = MinMaxScaler()
    df_scaled = df.copy()
    df_scaled[features] = scaler.fit_transform(df[features])
    
    persona_means = df_scaled.groupby('Persona')[features].mean()
    
    labels=np.array(features)
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    colors = sns.color_palette("husl", len(persona_means))
    
    for idx, (persona, row) in enumerate(persona_means.iterrows()):
        values = row.tolist()
        values += values[:1] 
        ax.plot(angles, values, color=colors[idx], linewidth=2, label=persona)
        ax.fill(angles, values, color=colors[idx], alpha=0.1)
    
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.title("Persona Behavioral Fingerprints (Normalized)", y=1.08)
    
    plt.savefig(RADAR_CHART_FILE, bbox_inches='tight', dpi=300)
    print(f"Saved radar chart to {RADAR_CHART_FILE}")
    plt.close()

def plot_tsne(df):
    print("Generating t-SNE Plot (this may take a moment)...")
    
    feature_cols = [
        'tx_count', 'active_days', 'avg_tx_per_day', 'total_gas_spent',
        'total_nft_buys', 'total_nft_sells', 'total_nft_volume_usd',
        'unique_nfts_owned', 'dex_trades', 'avg_trade_size_usd',
        'total_traded_usd', 'erc20_receive_usd', 'erc20_send_usd',
        'native_balance_delta'
    ]
    
    X = df[feature_cols].fillna(0)
    
    tsne = TSNE(n_components=2, random_state=42, init='random', learning_rate='auto')
    X_embedded = tsne.fit_transform(X)
    
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        x=X_embedded[:, 0], 
        y=X_embedded[:, 1], 
        hue=df['Persona'], 
        palette='husl',
        alpha=0.7
    )
    
    plt.title("t-SNE Projection of Wallet Clusters")
    plt.xlabel("Dimension 1")
    plt.ylabel("Dimension 2")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(TSNE_PLOT_FILE, dpi=300)
    print(f"Saved t-SNE plot to {TSNE_PLOT_FILE}")
    plt.close()

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        plot_radar_chart(df)
        plot_tsne(df)
        print("Visualization complete.")
