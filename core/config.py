import os
import streamlit as st
from dotenv import load_dotenv


#load .env only in local dev
# if not st.secrets:
#     load_dotenv()

from dotenv import load_dotenv

def get_config(key: str, default: str = None) -> str:
    try:
        # Try Streamlit secrets first
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # If st.secrets is missing or empty, load from .env
        load_dotenv()
        return os.getenv(key, default)


def get_config(key: str, default: str = None) -> str:
    return os.getenv(key, default)

# --- API KEYS ---
def get_groq_api_key():
    return st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

# --- MODEL CONFIG ---
EMBEDDING_MODEL = get_config(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

LLM_PROVIDER = get_config("LLM_PROVIDER", "groq")
LLM_MODEL = get_config("LLM_MODEL", "llama-3.1-8b-instant")
LLM_TEMPERATURE = float(get_config("LLM_TEMPERATURE", 0.5))

# --- PATHS ---
PERSIST_DIRECTORY = get_config("PERSIST_DIRECTORY", "./chroma_db")

def validate_config():
    errors = []

    if LLM_PROVIDER == "groq" and not get_groq_api_key():
        errors.append("GROQ_API_KEY is required for Groq provider")

    # if LLM_PROVIDER == "huggingface" and not HUGGINGFACE_API_KEY:
    #     errors.append("HUGGINGFACE_API_KEY is required")

    if not LLM_PROVIDER:
        errors.append("LLM_PROVIDER must be set")

    if errors:
        raise ValueError(
            "Configuration errors:\n" +
            "\n".join(f"- {e}" for e in errors)
        )