import os
import logging
from fastapi import FastAPI, Request, HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow as Flow
from googleapiclient.discovery import build
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this if you have specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Adjust if you want to restrict to POST, GET, etc.
    allow_headers=["*"],  # You may specify particular headers if needed
)

# Define scopes and load client secrets directly from environment variables
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS_INFO = {
    "installed": {
        "client_id": os.getenv("CLIENT_ID"),
        "project_id": os.getenv("PROJECT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "redirect_uris": [os.getenv("REDIRECT_URIS")]
    }
}

# Same token storage functions as before

@app.get("/login")
def login():
    flow = Flow.from_client_config(
        CLIENT_SECRETS_INFO,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URIS")
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    logging.info(f"Generated authentication URL: {auth_url}")
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        logging.error("No code parameter found in request")
        raise HTTPException(status_code=400, detail="Missing code parameter.")
    
    flow = Flow.from_client_config(
        CLIENT_SECRETS_INFO,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URIS")
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    token_info = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    save_token_info(token_info)
    logging.info("Authentication successful and token info saved")
    return {"message": "Authentication successful"}

@app.get("/get-playlist-videos")
def get_playlist_videos(playlist_id: str):
    token_info = load_token_info()
    if not token_info:
        logging.warning("No token info available, authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")

    credentials = Credentials(**token_info)
    youtube = build("youtube", "v3", credentials=credentials)
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=10
    )
    response = request.execute()
    logging.info("Retrieved playlist videos successfully")
    return response
