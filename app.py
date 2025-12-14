from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.inference import ClusterPredictor
from src.llm import PersonaExplainer
import os
import requests
import uuid
from dotenv import load_dotenv
from diskcache import Cache
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

app = FastAPI(title="Crypto Wallet Persona API", description="Async API with AI-powered Wallet Analysis.")

origins = [
    "http://localhost",
    "http://localhost:5173", # Default Vite port
    "http://localhost:5173", # Vite port when accessed via IP
    "YOUR_VERCEL_FRONTEND_URL" # Placeholder for your Vercel frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & Initialization ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "kmeans_model.pkl")
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "wallet_power_transformer.pkl")
CACHE_DIR = os.path.join(BASE_DIR, "cache_data")

# Initialize Components
cache = Cache(CACHE_DIR)
# Expire cache entries after 24 hours (86400 seconds)
CACHE_TTL = 86400 

try:
    predictor = ClusterPredictor(model_path=MODEL_PATH, preprocessor_path=PREPROCESSOR_PATH)
    explainer = PersonaExplainer()
except FileNotFoundError as e:
    print(f"Startup Error: {e}")
    predictor = None
    explainer = None

# --- Models ---
class JobResponse(BaseModel):
    job_id: str
    status: str # "queued", "processing", "completed", "failed"
    wallet_address: str

class AnalysisResult(BaseModel):
    status: str
    wallet_address: Optional[str] = None
    persona: Optional[str] = None
    confidence_scores: Optional[Dict[str, float]] = None
    explanation: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# --- Background Worker ---
def process_wallet_analysis(job_id: str, wallet_address: str):
    """
    Background task that fetches data, predicts persona, and generates AI explanation.
    Updates the cache state as it progresses.
    """
    try:
        # Update status to processing
        cache.set(job_id, {"status": "processing", "wallet": wallet_address}, expire=CACHE_TTL)
        
        # 1. Fetch Data from Dune
        if not DUNE_API_KEY:
            raise Exception("Dune API Key missing configuration.")

        dune_url = f"https://api.dune.com/api/v1/query/6252521/results?wallet={wallet_address}"
        headers = {"X-Dune-API-Key": DUNE_API_KEY}
        
        print(f"Fetching Dune data for {wallet_address}...")
        response = requests.get(dune_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"Dune API Error: {response.status_code} - {response.text}")

        data_json = response.json()
        if not data_json.get("result", {}).get("rows"):
            raise Exception("Wallet not found in Dune dataset (no activity).")
            
        row_data = data_json["result"]["rows"][0]
        
        # 2. Prepare Features & Predict
        if predictor is None:
             raise Exception("Inference Model not loaded.")

        model_input = {}
        for feature in predictor.FEATURES:
            val = row_data.get(feature)
            model_input[feature] = float(val) if val is not None else 0.0

        # Run Inference
        prediction_result = predictor.predict(model_input)
        # Result format: {'cluster_label': 3, 'persona': 'Whale', 'probabilities': {...}}
        
        # 3. Generate AI Explanation
        explanation = "AI Analysis unavailable."
        if explainer:
            explanation = explainer.generate_explanation(
                prediction_result['persona'], 
                model_input
            )

        # 4. Save Final Result to Cache
        final_result = {
            "status": "completed",
            "wallet_address": wallet_address,
            "persona": prediction_result['persona'],
            "confidence_scores": prediction_result['probabilities'],
            "explanation": explanation,
            "stats": model_input
        }
        
        # Cache key for the JOB
        cache.set(job_id, final_result, expire=CACHE_TTL)
        
        # ALSO Cache key for the WALLET (for instant lookup later)
        # We prefix with 'wallet:' to distinguish from job_ids
        cache.set(f"wallet:{wallet_address}", final_result, expire=CACHE_TTL)
        print(f"Job {job_id} completed successfully.")

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        error_state = {
            "status": "failed", 
            "wallet_address": wallet_address,
            "error": str(e)
        }
        cache.set(job_id, error_state, expire=CACHE_TTL)

# --- Endpoints ---

@app.get("/")
def home():
    return {"message": "Crypto Persona API (Async + AI). Use POST /analyze/start/{wallet} to begin."}

@app.post("/analyze/start/{wallet_address}", response_model=JobResponse)
def start_analysis(wallet_address: str, background_tasks: BackgroundTasks):
    """
    Starts the analysis job. Returns a job_id immediately.
    Checks cache first for instant results.
    """
    # 1. Check Cache for this wallet
    cached_result = cache.get(f"wallet:{wallet_address}")
    if cached_result and cached_result['status'] == 'completed':
        # Create a "virtual" completed job for API consistency
        # Or we could just return the result directly? 
        # For this pattern, let's return a completed job_id that points to this data
        job_id = f"cached_{uuid.uuid4().hex[:8]}"
        cache.set(job_id, cached_result, expire=300) # Short TTL for temp job pointer
        return {"job_id": job_id, "status": "completed", "wallet_address": wallet_address}

    # 2. Start New Job
    job_id = str(uuid.uuid4())
    cache.set(job_id, {"status": "queued", "wallet": wallet_address}, expire=CACHE_TTL)
    
    background_tasks.add_task(process_wallet_analysis, job_id, wallet_address)
    
    return {"job_id": job_id, "status": "queued", "wallet_address": wallet_address}

@app.get("/analyze/status/{job_id}", response_model=AnalysisResult)
def check_status(job_id: str):
    """
    Poll this endpoint to get the result.
    """
    result = cache.get(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job ID not found or expired.")
    
    return result