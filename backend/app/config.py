from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL = os.getenv("MODEL", "claude-haiku-4-5")
MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", "20"))

BUCKETS = ["SIC", "BC", "School", "Options", "Lab", "Personal"]
PRIORITY_MIN = 0.0
PRIORITY_MAX = 10.0
