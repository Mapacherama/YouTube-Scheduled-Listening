import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import InstalledAppFlow as Flow
from googleapiclient.discovery import build
from pydantic import BaseModel
from dotenv import load_dotenv

from token_management import load_token_info, save_token_info, refresh_access_token, is_token_valid

load_dotenv()

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
        "redirect_uris": [os.getenv("REDIRECT_URI")]
    }
}

class CallbackResponse(BaseModel):
    message: str

@app.get("/login")
def login():
    flow = Flow.from_client_config(
        CLIENT_SECRETS_INFO,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URI")
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    logging.info(f"Generated authentication URL: {auth_url}")
    return RedirectResponse(auth_url)

@app.get("/callback", response_model=CallbackResponse)
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        logging.error("No code parameter found in request")
        raise HTTPException(status_code=400, detail="Missing code parameter.")
    
    flow = Flow.from_client_config(
        CLIENT_SECRETS_INFO,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URI")
    )
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
    except Exception as e:
        logging.error(f"Failed to fetch token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch token: {str(e)}")

    token_info = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    
    save_token_info(token_info)
    logging.info("Authentication successful and token info saved")
    
    return CallbackResponse(message="Authentication successful")

@app.get("/get-my-channel")
def get_my_channel():
    token_info = load_token_info() 
    if not token_info:
        logging.warning("No token info available, authentication required.")
        raise HTTPException(status_code=401, detail="Authentication required")

    if not is_token_valid(token_info):
        logging.info("Token invalid or expired, attempting refresh.")
        token_info = refresh_access_token(token_info)
        if not token_info:
            logging.warning("Failed to refresh token, authentication required.")
            raise HTTPException(status_code=401, detail="Authentication required")

    try:
        credentials = Credentials(**token_info)
        youtube = build("youtube", "v3", credentials=credentials)
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        return response
    except Exception as e:
        logging.error(f"Error retrieving channel info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving channel info")
