import pandas as pd
from sklearn.preprocessing import PowerTransformer
from sklearn.cluster import KMeans
import joblib
import os
from tqdm import tqdm
import time

DATA_PATH = "wallet_dataset.csv"
PREPROCESSOR_PATH = "wallet_power_transformer.pkl"
MODEL_PATH = "kmeans_model.pkl"
OUTPUT_LABELED_DATA_PATH = "wallet_dataset_labeled.csv"
N_CLUSTERS = 4
RANDOM_STATE = 42

FEATURES = [
    'tx_count', 'active_days', 'avg_tx_per_day', 'total_gas_spent',
    'total_nft_buys', 'total_nft_sells', 'total_nft_volume_usd',
    'unique_nfts_owned', 'dex_trades', 'avg_trade_size_usd',
    'total_traded_usd', 'erc20_receive_usd', 'erc20_send_usd',
    'native_balance_delta'
]

PERSONA_MAPPING = {
    0: "High-Frequency Bots / Automated Traders",
    1: "High-Value NFT & Crypto Traders (Degen Whales)",
    2: "Active Retail Users / Everyday Traders",
    3: "Ultra-Whales / Institutional & Exchange Wallets"
}

def train_model():
    print("Starting model training process...")
    
    steps = [
        "Load Data",
        "Preprocessing",
        "Train KMeans",
        "Apply Mapping",
        "Save Data"
    ]
    
    with tqdm(total=len(steps), desc="Training Pipeline") as pbar:
        
        pbar.set_description(f"Step: {steps[0]}")
        try:
            df = pd.read_csv(DATA_PATH)
        except FileNotFoundError:
            print(f"Error: {DATA_PATH} not found. Please ensure the raw data is available.")
            return
        pbar.update(1)

        X = df[FEATURES]

        pbar.set_description(f"Step: {steps[1]}")
        preprocessor = PowerTransformer(method='yeo-johnson')
        X_transformed = preprocessor.fit_transform(X)

        joblib.dump(preprocessor, PREPROCESSOR_PATH)
        pbar.update(1)

        pbar.set_description(f"Step: {steps[2]}")
        kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init='auto')
        df['Cluster_labels'] = kmeans.fit_predict(X_transformed)

        joblib.dump(kmeans, MODEL_PATH)
        pbar.update(1)

        pbar.set_description(f"Step: {steps[3]}")

        df['Persona'] = df['Cluster_labels'].map(PERSONA_MAPPING)
        pbar.update(1)

        pbar.set_description(f"Step: {steps[4]}")
        df.to_csv(OUTPUT_LABELED_DATA_PATH, index=False)
        pbar.update(1)
        
    print("\nModel training and data labeling complete.")

if __name__ == "__main__":
    train_model()
