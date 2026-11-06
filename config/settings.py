import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

# Application Configuration
APP_NAME = "EchoVerse AI"
APP_VERSION = "1.0.0"

# Conversation Memory Configuration
MAX_HISTORY_MESSAGES = 20