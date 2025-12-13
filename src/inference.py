import pandas as pd
import joblib
import os
import numpy as np

class ClusterPredictor:
    def __init__(self, model_path: str, preprocessor_path: str):
        self.model_path = model_path
        self.preprocessor_path = preprocessor_path
        self.model = None
        self.preprocessor = None
        
        self.FEATURES = [
            'tx_count', 'active_days', 'avg_tx_per_day', 'total_gas_spent',
            'total_nft_buys', 'total_nft_sells', 'total_nft_volume_usd',
            'unique_nfts_owned', 'dex_trades', 'avg_trade_size_usd',
            'total_traded_usd', 'erc20_receive_usd', 'erc20_send_usd',
            'native_balance_delta'
        ]
        
        self.PERSONA_MAPPING = {
            0: "High-Frequency Bots / Automated Traders",
            1: "High-Value NFT & Crypto Traders (Degen Whales)",
            2: "Active Retail Users / Everyday Traders",
            3: "Ultra-Whales / Institutional & Exchange Wallets"
        }
        
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads the model and preprocessor from disk."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        if not os.path.exists(self.preprocessor_path):
            raise FileNotFoundError(f"Preprocessor file not found at {self.preprocessor_path}")
            
        print(f"Loading model from {self.model_path}...")
        self.model = joblib.load(self.model_path)
        print(f"Loading preprocessor from {self.preprocessor_path}...")
        self.preprocessor = joblib.load(self.preprocessor_path)

    def predict(self, data: dict | pd.DataFrame) -> dict:
        """
        Predicts the persona for the given wallet data and provides probability scores.
        
        Args:
            data: A dictionary or DataFrame containing the required features.
            
        Returns:
            A dictionary (or list of dicts) containing:
            - cluster_label: The predicted cluster ID.
            - persona: The human-readable persona name.
            - probabilities: A dictionary mapping each persona to its confidence score (0-1).
        """
        import numpy as np
        from scipy.special import softmax

        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("Input data must be a dictionary or pandas DataFrame.")
            
        missing_cols = set(self.FEATURES) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required features: {missing_cols}")
            
        X = df[self.FEATURES]
        
        X_transformed = self.preprocessor.transform(X)
        
        # 1. Hard Prediction (Cluster Label)
        cluster_labels = self.model.predict(X_transformed)
        
        # 2. Soft Probability (Distance-based)
        # transform() returns distance to each cluster center
        distances = self.model.transform(X_transformed)
        
        # We want closer distance = higher probability.
        # So we take the negative distance.
        # We apply softmax to normalize into a probability distribution (sum=1).
        # Multiplying by a factor (e.g., -1 or -2) can sharpen the probabilities.
        # Using -1 * distance is standard for "soft k-means".
        probs = softmax(-distances, axis=1)
        
        results = []
        for i, label in enumerate(cluster_labels):
            prob_dict = {
                self.PERSONA_MAPPING.get(c_idx, f"Cluster {c_idx}"): float(probs[i][c_idx])
                for c_idx in range(probs.shape[1])
            }
            
            results.append({
                "cluster_label": int(label),
                "persona": self.PERSONA_MAPPING.get(label, "Unknown"),
                "probabilities": prob_dict
            })
            
        if len(results) == 1:
            return results[0]
        return results
