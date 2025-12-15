---
title: Cluster Protocol
emoji: 🔥
colorFrom: indigo
colorTo: red
sdk: docker
pinned: false
license: mit
short_description: Behavioral clustering engine for Web3 wallets
---

# Crypto Wallet Clustering

Unsupervised machine learning project to segment cryptocurrency wallets into behavioral personas (e.g., "Whales", "NFT Flippers", "Dormant") based on on-chain transaction data.

## ❓ The Problem
In the Web3 ecosystem, users are anonymous by default. A wallet address (`0x123...`) gives no indication of whether the user is a high-value institution, a retail trader, a bot, or an NFT collector. 
*   **Marketing is blind:** Projects cannot target specific users effectively.
*   **Risk is opaque:** Protocols cannot easily distinguish between organic users and sybil attackers.
*   **Data is noisy:** Raw transaction logs are massive and unreadable without advanced processing.

## 💡 The Solution: Cluster Protocol
**Cluster Protocol** is an AI-powered engine that "fingerprints" wallets based on their behavior, not their identity.
1.  **Ingest:** Pulls raw on-chain data (Gas spent, NFT volume, DEX trades, etc.) via Dune Analytics.
2.  **Process:** Normalizes skewed financial data using **Yeo-Johnson Power Transformations**.
3.  **Cluster:** Uses **K-Means Clustering** to mathematically group similar wallets.
4.  **Label:** Assigns a human-readable persona (e.g., "Active Retail", "High-Frequency Bot") with a confidence score.

## Key Features
- **Robust Preprocessing:** Handles extreme data skewness (common in financial data) using **Yeo-Johnson Power Transformation**.
- **Smart Filtering:** Heuristic detection to separate **Smart Contracts** from **EOAs** (Externally Owned Accounts).
- **Model Selection:** Benchmarked K-Means, DBSCAN, and GMM. **K-Means (K=4)** was selected as the production model.
- **Inference with Confidence:** Predicts personas for new wallets and provides **probability scores** (e.g., "85% Whale, 15% Trader").
- **Automated Retraining:** GitHub Actions workflow automatically fetches new data and retrains the model weekly to handle data drift.
- **End-to-End API:** Fetch data from Dune and classify a wallet in a single API call.

## ⚠️ Supported Networks
**Cluster Protocol currently supports Ethereum Mainnet (L1) only.**
*   **Supported:** Ethereum (`0x...`).
*   **Not Supported:** L2s (Arbitrum, Optimism, Base), Sidechains (Polygon), or Non-EVM chains (Solana, Bitcoin).
*   **Note:** The engine analyzes the last **2 Years** of history for DeFi/NFTs to ensure relevance and speed.

## Tech Stack
- **Python 3.10+**
- **Pandas & NumPy** (Data manipulation)
- **Scikit-Learn** (Clustering & Preprocessing)
- **Matplotlib & Seaborn** (Visualization)
- **FastAPI** (Inference API)
- **Dune API** (Data ingestion)
- **GitHub Actions** (CI/CD & Automation)

## Project Structure
```
cluster/
├── data/                   # Dataset storage
├── docs/                   # Visualizations & Images
├── notebooks/              # Jupyter notebooks for EDA and modeling
├── src/                    # Core logic (Inference Engine)
├── .github/workflows/      # Automated retraining workflows
├── app.py                  # FastAPI Endpoint
├── predict.py              # CLI Inference Tool
├── train.py                # Production training pipeline
├── request.py              # Script to fetch data from Dune
├── README.md               # Project documentation
└── PROJECT_LOG.md          # Engineering log & decision records
```

## Identified Personas
The model identified 4 distinct behavioral clusters:

1.  **Ultra-Whales / Institutional & Exchange Wallets** (Cluster 3)
    *   *Characteristics:* Massive volume, extremely high transaction counts.
2.  **Active Retail Users / Everyday Traders** (Cluster 2)
    *   *Characteristics:* Consistent daily activity, moderate volume.
3.  **High-Frequency Bots / Automated Traders** (Cluster 1)
    *   *Characteristics:* High transaction count but low human-like variety.
4.  **High-Value NFT & Crypto Traders (Degen Whales)** (Cluster 0)
    *   *Characteristics:* High risk, high NFT volume, specialized activity.

### Visualizations
**t-SNE Projection of Clusters**
![t-SNE Plot](docs/clusters_tsne.png)

**Behavioral Radar Chart**
![Radar Chart](docs/persona_radar_chart.png)

## Getting Started

### Prerequisites
- Python 3.10+
- `uv` (recommended)
- Dune Analytics API Key (for fetching new data)

### Installation
```bash
git clone <repo-url>
cd cluster
uv sync
```
Create a `.env` file with your API key:
```
DUNE_API_KEY=your_key_here
```

### Usage

#### 1. Train the Model
Run the production pipeline to train K-Means and save artifacts (`kmeans_model.pkl`, `wallet_power_transformer.pkl`).
```bash
uv run train.py
```

#### 2. Make Predictions (CLI)
Classify a specific wallet (or row from the dataset) and see confidence scores.
```bash
uv run predict.py --row 0
# Output:
# Cluster: 3
# Persona: Ultra-Whales / Institutional
# Confidence: Ultra-Whales: 0.52, Retail: 0.26...
```

#### 3. Run the API
Start the FastAPI server for real-time inference.
```bash
uv run uvicorn app:app --reload
```
**Analyze a specific wallet (Fetch + Predict):**
```bash
curl "http://localhost:8000/analyze/0x123...abc"
```

#### 4. Visualize Results
Generate fresh t-SNE and Radar charts.
```bash
uv run visualize_clusters.py
```