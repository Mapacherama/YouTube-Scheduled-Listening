import os
import json
import logging
from datetime import datetime

token_store = {}
TOKEN_FILE_PATH = "token_info.json"

def save_token_info(token_info):
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
        expires_at = datetime.fromisoformat(token_info['expires_at'])
        return expires_at > datetime.now()
    return False 