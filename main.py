import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow as Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

from token_management import save_token_info, load_token_info, is_token_valid

app = FastAPI()

logging.basicConfig(level=logging.INFO)

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
        "scopes": credentials.scopes,
        "expires_at": credentials.expiry.isoformat()
    }
    
    save_token_info(token_info)
    logging.info("Authentication successful and token info saved")
    
    return {"message": "Authentication successful"}

@app.get("/get-playlist-videos")
def get_playlist_videos(playlist_id: str):
    token_info = load_token_info()
    if token_info is None:
        logging.warning("No token info available, authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")

    token_info = refresh_access_token(token_info)
    
    try:
        credentials = Credentials(**token_info)
        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=10
        )
        response = request.execute()
        return {
            "videos": response.get("items", []),
            "totalResults": response.get("pageInfo", {}).get("totalResults", 0)
        }
    except Exception as e:
        logging.error(f"Error retrieving playlist videos: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving playlist videos")

def refresh_access_token(token_info):
    credentials = Credentials(**token_info)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        new_token_info = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expires_at": credentials.expiry.isoformat()
        }
        save_token_info(new_token_info)
        return new_token_info
    return token_info
