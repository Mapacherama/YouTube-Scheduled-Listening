import os
import logging
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from token_management import load_token_info, save_token_info

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

def is_token_valid(token_info):
    credentials = Credentials(**token_info)
    if not credentials:
        logging.warning("No credentials found.")
        return False
    if credentials.expired:
        logging.info("Token is expired.")
        return False
    if not credentials.refresh_token:
        logging.warning("No refresh token available.")
        return False
    logging.info("Token is valid.")
    return True