import os
import asyncio
import dropbox
from auth import refresh_access_token_async, load_allowed_user_ids_from_dropbox
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Set environment variables and API keys
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    ELEVEN_API_KEY = os.environ["ELEVEN_API_KEY"]
    BING_API_KEY = os.environ["BING_API_KEY"]
    DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
    STABILITY_API_KEY = os.environ["STABILITY_API_KEY"]
    WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    DROPBOX_REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]
    DROPBOX_CLIENT_ID = os.environ["DROPBOX_CLIENT_ID"]
    DROPBOX_CLIENT_SECRET = os.environ["DROPBOX_CLIENT_SECRET"]
    ALLOWED_USER_IDS = [1264710221, 319092783, 1147606131, 1123137330]
    DROPBOX_ACCESS_TOKEN = asyncio.run(refresh_access_token_async(DROPBOX_REFRESH_TOKEN, DROPBOX_CLIENT_ID, DROPBOX_CLIENT_SECRET))
    
    # Initialize Dropbox client on startup
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    AUTHORIZED_USER_IDS = asyncio.run(load_allowed_user_ids_from_dropbox(dbx))
    
    