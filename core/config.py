from dotenv import load_dotenv
load_dotenv(override=True)
import os

LLM_MODEL = "gpt-4o"

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SHOW_PRIVATE_ROLES = False
PRIVATE_ROLES_PATTERN_MATCH = None # ["💼"] # list of all strings pattern that match with roles names will be displayed