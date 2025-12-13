from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.inference import ClusterPredictor
import os
import requests
from dotenv import load_dotenv

load_dotenv()
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

app = FastAPI(title="Crypto Wallet Persona API", description="API to classify crypto wallets into behavioral personas.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "kmeans_model.pkl")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "wallet_power_transformer.pkl")

try:
    predictor = ClusterPredictor(model_path=MODEL_PATH, preprocessor_path=PREPROCESSOR_PATH)
except FileNotFoundError as e:
    print(f"Startup Error: {e}")
    predictor = None

class WalletFeatures(BaseModel):
    tx_count: float
    active_days: float
    avg_tx_per_day: float
    total_gas_spent: float
    total_nft_buys: float
    total_nft_sells: float
    total_nft_volume_usd: float
    unique_nfts_owned: float
    dex_trades: float
    avg_trade_size_usd: float
    total_traded_usd: float
    erc20_receive_usd: float
    erc20_send_usd: float
    native_balance_delta: float

    class Config:
        json_schema_extra = {
            "example": {
                "tx_count": 1767.0,
                "active_days": 90.0,
                "avg_tx_per_day": 19.6,
                "total_gas_spent": 0.75,
                "total_nft_buys": 17963024.0,
                "total_nft_sells": 17558.0,
                "total_nft_volume_usd": 384457660.0,
                "unique_nfts_owned": 112763.0,
                "dex_trades": 10150882.0,
                "avg_trade_size_usd": 107.0,
                "total_traded_usd": 1048649651.0,
                "erc20_receive_usd": 1148467065414998.0,
                "erc20_send_usd": 120143.0,
                "native_balance_delta": 0.23
            }
        }

@app.get("/")
def home():
    return {"message": "Crypto Wallet Persona API is running. Use /analyze/{wallet_address} to fetch and classify."}

@app.post("/predict")
def predict_persona(features: WalletFeatures):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not initialized. Check server logs.")
    
    try:
        data = features.model_dump()
        result = predictor.predict(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/{wallet_address}")
def analyze_wallet(wallet_address: str):
    """
    Fetches wallet data from Dune Analytics and predicts its persona.
    """
    if not DUNE_API_KEY:
         raise HTTPException(status_code=500, detail="Dune API Key not configured on server.")

    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not initialized.")

    dune_url = f"https://api.dune.com/api/v1/query/6252521/results?wallet={wallet_address}"
    headers = {"X-Dune-API-Key": DUNE_API_KEY}
    
    try:
        print(f"Fetching data for {wallet_address} from Dune...")
        response = requests.get(dune_url, headers=headers, timeout=10)
        
        if response.status_code == 429:
             raise HTTPException(status_code=429, detail="Dune API Rate Limit Exceeded. Please try again later.")
        if response.status_code != 200:
             raise HTTPException(status_code=response.status_code, detail=f"Dune API Error: {response.text}")
             
        data = response.json()
        
        if not data.get("result", {}).get("rows"):
             raise HTTPException(status_code=404, detail="Wallet not found in Dune dataset (or no activity found).")
             
        row_data = data["result"]["rows"][0]
        
        # 2. Map Dune Data to Model Features
        # The column names from Dune (active_days, etc.) generally match our features.
        # We construct the dictionary carefully to ensure all features are present.
        # If Dune sends nulls, we default to 0.0
        model_input = {}
        missing_features = []
        
        for feature in predictor.FEATURES:
            if feature in row_data:
                val = row_data[feature]
                model_input[feature] = float(val) if val is not None else 0.0
            else:
                missing_features.append(feature)
        
        if missing_features:
            print(f"Warning: Missing features from Dune response: {missing_features}")
            for f in missing_features:
                model_input[f] = 0.0

        result = predictor.predict(model_input)
        
        return {
            "wallet_address": wallet_address,
            "dune_data": model_input,
            "prediction": result
        }

    except requests.RequestException as e:
        print(f"Request Error: {e}")
        raise HTTPException(status_code=502, detail="Failed to connect to Dune API.")
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
