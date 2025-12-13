import argparse
import pandas as pd
from src.inference import ClusterPredictor
import os

def main():
    parser = argparse.ArgumentParser(description="Predict personas for crypto wallets.")
    parser.add_argument("--file", type=str, help="Path to a CSV file containing wallet features.")
    parser.add_argument("--row", type=int, default=0, help="Row index to use from the dataset if no file is provided (uses wallet_dataset.csv).")
    args = parser.parse_args()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "kmeans_model.pkl")
    PREPROCESSOR_PATH = os.path.join(BASE_DIR, "wallet_power_transformer.pkl")
    DEFAULT_DATA_PATH = os.path.join(BASE_DIR, "wallet_dataset.csv")

    try:
        predictor = ClusterPredictor(model_path=MODEL_PATH, preprocessor_path=PREPROCESSOR_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    if args.file:
        input_path = args.file
        if not os.path.exists(input_path):
            print(f"Error: File {input_path} not found.")
            return
        print(f"Processing file: {input_path}")
        df = pd.read_csv(input_path)
        
        try:
            results = predictor.predict(df)
            if isinstance(results, list):
                df['Predicted_Cluster'] = [r['cluster_label'] for r in results]
                df['Predicted_Persona'] = [r['persona'] for r in results]
            else:
                 df['Predicted_Cluster'] = results['cluster_label']
                 df['Predicted_Persona'] = results['persona']
                 
            output_path = input_path.replace(".csv", "_predicted.csv")
            df.to_csv(output_path, index=False)
            print(f"Predictions saved to {output_path}")
        except Exception as e:
            print(f"Prediction error: {e}")

    else:
        print(f"No input file provided. Using row {args.row} from {DEFAULT_DATA_PATH} as a sample.")
        if not os.path.exists(DEFAULT_DATA_PATH):
            print("Default dataset not found.")
            return
            
        df = pd.read_csv(DEFAULT_DATA_PATH)
        if args.row >= len(df):
            print(f"Row {args.row} out of bounds.")
            return
            
        sample = df.iloc[args.row].to_dict()
        print("\n--- Sample Features ---")
        for k, v in sample.items():
            if k in predictor.FEATURES:
                print(f"{k}: {v}")
                
        try:
            result = predictor.predict(sample)
            print("\n--- Prediction Result ---")
            print(f"Cluster: {result['cluster_label']}")
            print(f"Persona: {result['persona']}")
            
            print("\n--- Confidence Scores ---")
            sorted_probs = sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True)
            for persona, score in sorted_probs:
                print(f"{persona}: {score:.4f}")
                
        except Exception as e:
            print(f"Prediction error: {e}")

if __name__ == "__main__":
    main()
