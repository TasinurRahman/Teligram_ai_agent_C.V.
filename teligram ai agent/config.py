import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "6539634793")

# LLM API Configuration (Supports Groq, OpenRouter, or Local Ollama)
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "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")

# Specialist Open-Source Models Mapping (Groq / OpenRouter Compatible)
if "groq.com" in LLM_API_BASE:
    MODEL_SPECIALISTS = {
        "reasoning": "openai/gpt-oss-120b", # GPT-OSS 120B on Groq (Ultra-Fast 120B reasoning)
        "coding": "qwen/qwen3.8-27b",      # Qwen 27B on Groq (Coding Specialist)
        "general": "openai/gpt-oss-20b"     # GPT-OSS 20B on Groq (Ultra-Fast General Assistant)
    }
else:
    MODEL_SPECIALISTS = {
        "reasoning": "deepseek/deepseek-r1",          # DeepSeek-R1 on OpenRouter / Ollama
        "coding": "qwen/qwen-2.5-coder-32b-instruct", # Qwen 2.5 Coder
        "general": "meta-llama/llama-3.3-70b-instruct" # LLaMA 3.3 70B
    }

# Database Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)

SQLITE_DB_PATH = os.path.join(DB_DIR, "agent.db")
CHROMADB_PATH = os.path.join(DB_DIR, "chroma_db")

# Default User Limits
DEFAULT_DAILY_REQUEST_LIMIT = 50  # For non-admin Telegram users
