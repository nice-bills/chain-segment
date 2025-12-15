from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.inference import ClusterPredictor
from src.llm import PersonaExplainer
import os
import requests
import uuid
import time
from dotenv import load_dotenv
from diskcache import Cache
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Crypto Wallet Persona API", description="Async API with AI-powered Wallet Analysis.")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost",
    "http://localhost:5173", # Default Vite port
    "http://localhost:5173", # Vite port when accessed via IP
    "http://127.0.0.1:5173", # Vite port when accessed via IP
]

# Add Vercel Frontend URL from Env (if set)
vercel_frontend = os.getenv("FRONTEND_URL")
if vercel_frontend:
    origins.append(vercel_frontend)

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
        
        # 1. Execute Dune Query (Start New Run)
        if not DUNE_API_KEY:
            raise Exception("Dune API Key missing configuration.")

        # Step A: Submit Execution
        execute_url = "https://api.dune.com/api/v1/query/6252521/execute"
        headers = {"X-Dune-API-Key": DUNE_API_KEY}
        payload = {"query_parameters": {"wallet": wallet_address}}
        
        print(f"Submitting Dune query for {wallet_address}...")
        exec_res = requests.post(execute_url, headers=headers, json=payload, timeout=10)
        
        if exec_res.status_code != 200:
            raise Exception(f"Dune Execution Failed: {exec_res.status_code} - {exec_res.text}")
            
        execution_id = exec_res.json().get("execution_id")
        if not execution_id:
            raise Exception("No execution_id returned from Dune.")

        # Step B: Poll for Completion
        print(f"Polling Dune execution {execution_id}...")
        status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
        
        max_retries = 30 # 30 * 2s = 60s max wait
        for i in range(max_retries):
            status_res = requests.get(status_url, headers=headers, timeout=10)
            if status_res.status_code != 200:
                 # Temporary network glitch? Wait and retry.
                 time.sleep(2)
                 continue
                 
            state = status_res.json().get("state")
            if state == "QUERY_STATE_COMPLETED":
                break
            elif state == "QUERY_STATE_FAILED":
                raise Exception("Dune Query Execution FAILED internally.")
            elif state == "QUERY_STATE_CANCELLED":
                raise Exception("Dune Query was CANCELLED.")
                
            time.sleep(2)
        else:
            raise Exception("Dune Query Timed Out (60s).")

        # Step C: Fetch Results
        results_url = f"https://api.dune.com/api/v1/execution/{execution_id}/results"
        results_res = requests.get(results_url, headers=headers, timeout=15)
        
        if results_res.status_code != 200:
             raise Exception(f"Failed to fetch results: {results_res.status_code}")

        data_json = results_res.json()
        rows = data_json.get("result", {}).get("rows", [])
        
        if not rows:
            # If the query ran but returned no rows (maybe empty wallet?)
            # We can either fail or proceed with zero-filled data.
            # Given the SQL logic, it usually returns 1 row with 0s if empty, 
            # but let's be safe.
             raise Exception("Dune returned no data rows for this wallet.")
        
        # We trust the execution result because we just ran it with the param.
        row_data = rows[0]
            
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

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")

@app.post("/analyze/start/{wallet_address}", response_model=JobResponse)
@limiter.limit("5/minute")
def start_analysis(wallet_address: str, background_tasks: BackgroundTasks, request: Request):
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