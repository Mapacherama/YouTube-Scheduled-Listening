# YouTube API Integration with FastAPI

This project demonstrates how to integrate the YouTube Data API v3 with a FastAPI backend. It allows for OAuth authentication and interacting with YouTube features such as retrieving playlist data and videos.

## Project Structure

- **main.py**: The main FastAPI app file with YouTube API integration and token management.
- **token_management.py**: Contains functions for saving, loading, and validating OAuth token information.
- **env/**: Virtual environment for dependencies.
- **token_info.json**: Stores YouTube OAuth token information.

## Setup Instructions

1. Clone this repository.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use env\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install fastapi google-auth google-auth-oauthlib google-api-python-client python-dotenv
   ```
4. Create a `.env` file in the root directory and add your Google API credentials:
   ```plaintext
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   PROJECT_ID=your_project_id
   AUTH_URI=https://accounts.google.com/o/oauth2/auth
   TOKEN_URI=https://oauth2.googleapis.com/token
   AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
   REDIRECT_URIS=your_redirect_uri
   ```

## Usage

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
2. Navigate to `http://localhost:8000/login` to initiate the OAuth authentication process.
3. After successful authentication, you can retrieve playlist videos by accessing the endpoint:
   ```
   GET /get-playlist-videos?playlist_id=your_playlist_id
   ```

## Token Management

The application includes a token management system that handles saving, loading, and validating OAuth tokens. The token information is stored in `token_info.json`, and the application checks for token expiration before making API requests.

## Logging

The application uses logging to provide insights into the authentication process and API interactions. Logs are printed to the console for easy debugging.

## License

This project is licensed under the MIT License.
