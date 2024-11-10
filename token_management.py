import os
import json
import logging
from datetime import datetime
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
import pytz

token_store = {}
TOKEN_FILE_PATH = "token_info.json"

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

def save_token_info(token_info):
    logging.info(f"Saving token info: {token_info}")
    token_store['token_info'] = token_info
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_info, f)
    logging.info("Token information saved successfully.")

def load_token_info():
    if 'token_info' in token_store:
        if is_token_valid(token_store['token_info']):
            return token_store['token_info']
        else:
            logging.warning("Stored token is expired. Re-authentication is required.")
            return None

    if os.path.exists(TOKEN_FILE_PATH):
        try:
            with open(TOKEN_FILE_PATH, 'r') as f:
                token_info = json.load(f)
                logging.info(f"Loaded token info: {token_info}")
                if is_token_valid(token_info):
                    token_store['token_info'] = token_info
                    return token_info
                else:
                    logging.warning("Loaded token is expired. Re-authentication is required.")
                    return None
        except json.JSONDecodeError:
            logging.error("Invalid token file format. Re-authentication is required.")
            return None
    return None

def is_token_valid(token_info):
    if 'expires_at' in token_info:
        # Convert expires_at to an aware datetime
        expires_at = datetime.fromisoformat(token_info['expires_at']).astimezone(pytz.utc)
        logging.info(f"Checking if token is valid. Expires at: {expires_at}, Now: {datetime.now(pytz.utc)}")
        return expires_at > datetime.now(pytz.utc)  # Compare with aware datetime
    return False

def fetch_token(code):
    flow = Flow.from_client_config(
        CLIENT_SECRETS_INFO,
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URI")
    )
    flow.fetch_token(code=code)
    return flow.credentials

def refresh_access_token(token_info):
    credentials = Credentials(**token_info)
    if credentials.expired and credentials.refresh_token:
        logging.info(f"Attempting to refresh token: {credentials.refresh_token}")
        try:
            credentials.refresh(GoogleRequest())
            new_token_info = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token or token_info['refresh_token'],
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }
            save_token_info(new_token_info)
            logging.info("Token refreshed successfully.")
            return new_token_info
        except Exception as e:
            logging.error(f"Failed to refresh token: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh token")
    logging.warning("Token was not expired or no refresh token available.")
    return token_info