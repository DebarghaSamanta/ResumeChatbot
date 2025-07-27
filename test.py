from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY")
print("Loaded GROK_API_KEY:", GROK_API_KEY)
