import os
import time
from typing import Dict, Optional
from groq import Groq
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
load_dotenv()

class PersonaExplainer:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.hf_api_token = os.getenv("HF_API_TOKEN")
        
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.hf_client = InferenceClient(token=self.hf_api_token) if self.hf_api_token else None

    def generate_explanation(self, persona: str, stats: Dict[str, float]) -> str:
        """
        Generates a humorous/insightful explanation of the wallet's persona.
        """
        prompt = self._construct_prompt(persona, stats)
        
        # Try Groq First (Fastest)
        if self.groq_client:
            try:
                return self._call_groq(prompt)
            except Exception as e:
                print(f"Groq API failed: {e}. Falling back...")
        
        # Fallback to Hugging Face
        if self.hf_client:
            try:
                return self._call_hf(prompt)
            except Exception as e:
                print(f"HF API failed: {e}.")
        
        return "Analysis unavailable (AI models busy)."

    def _construct_prompt(self, persona: str, stats: Dict) -> str:
        # Simplify stats for the LLM to avoid token bloat
        key_stats = {
            "Transactions": int(stats.get('tx_count', 0)),
            "NFT Volume (USD)": f"${stats.get('total_nft_volume_usd', 0):,.2f}",
            "Gas Spent (ETH)": f"{stats.get('total_gas_spent', 0):.4f}",
            "Active Days": int(stats.get('active_days', 0)),
            "DEX Trades": int(stats.get('dex_trades', 0))
        }
        
        return (
            f"You are a crypto analytics bot with a witty, slightly roasting personality. "
            f"Analyze this wallet:\n"
            f"Persona: {persona}\n"
            f"Stats: {key_stats}\n\n"
            f"Task: Write a 2-3 sentence 'Roast' or 'Insight' about this user. "
            f"Explain WHY they fit this persona based on the stats. "
            f"Be specific but concise."
        )

    def _call_groq(self, prompt: str) -> str:
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a witty crypto analyst."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=200,
        )
        return chat_completion.choices[0].message.content

    def _call_hf(self, prompt: str) -> str:
        # Using Mistral-7B-Instruct via HF Inference API
        return self.hf_client.text_generation(
            prompt, 
            model="mistralai/Mistral-7B-Instruct-v0.2", 
            max_new_tokens=200,
            temperature=0.7
        )
