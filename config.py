import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
# Tests set this to an empty string so they stay on in-memory checkpoints.
_database_disabled = os.environ.get("ONBOARDING_DATABASE_URL") == ""
load_dotenv(ROOT / ".env", override=True)
if _database_disabled:
    os.environ["ONBOARDING_DATABASE_URL"] = ""

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ONBOARDING_DATABASE_URL = os.getenv("ONBOARDING_DATABASE_URL")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def get_llm():
    if not GROQ_API_KEY:
        return None
    import truststore
    from langchain_groq import ChatGroq

    # Company traffic is inspected by Zscaler. The Mac trust store already
    # accepts that certificate; the default Python bundle does not.
    truststore.inject_into_ssl()
    return ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
