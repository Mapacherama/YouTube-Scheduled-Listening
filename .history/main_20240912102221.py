import os
import json
from fastapi import FastAPI, Request, HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from fastapi.responses import RedirectResponse

app = FastAPI()

# Load client secrets from file
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# You can replace this with database storage for persistence
token_store = {}
TOKEN_FILE_PATH = "token_info.json"

def save_token_info(token_info):
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_info, f)

def load_token_info():
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, 'r') as f:
            return json.load(f)
    return None

@app.get("/login")
def login():
    # Initialize the flow with client secrets
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter.")
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
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
    return {"message": "Authentication successful"}

@app.get("/get-playlist-videos")
def get_playlist_videos(playlist_id: str):
    token_info = load_token_info()
    if not token_info:
        raise HTTPException(status_code=401, detail="Authentication required")

    credentials = Credentials(**token_info)
    youtube = build("youtube", "v3", credentials=credentials)

    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=10
    )
    response = request.execute()

    return response
