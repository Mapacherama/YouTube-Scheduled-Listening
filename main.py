import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyyoutube import Api
from dotenv import load_dotenv
import webbrowser
from datetime import datetime, timedelta
import pytz

load_dotenv()

app = FastAPI()
logging.basicConfig(level=logging.INFO)

api_key = os.getenv("YOUTUBE_API_KEY")
if not api_key:
    logging.error("YOUTUBE_API_KEY environment variable is not set.")
    raise RuntimeError("YOUTUBE_API_KEY environment variable is required.")

api = Api(api_key=api_key)

@app.get("/get-channel/{channel_id}")
def get_channel(channel_id: str):
    try:
        response = api.get_channel_info(channel_id=channel_id)
        if response.items:
            channel_info = response.items[0].to_dict()
            return channel_info
        else:
            logging.warning(f"No channel information found for ID: {channel_id}")
            raise HTTPException(status_code=404, detail="Channel not found")
    except Exception as e:
        logging.error(f"Error retrieving channel info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving channel info")

@app.get("/get-playlist/{playlist_id}")
def get_playlist(playlist_id: str):
    try:
        response = api.get_playlist_by_id(playlist_id=playlist_id)
        if response.items:
            playlist_info = response.items[0].to_dict()
            return playlist_info
        else:
            logging.warning(f"No playlist information found for ID: {playlist_id}")
            raise HTTPException(status_code=404, detail="Playlist not found")
    except Exception as e:
        logging.error(f"Error retrieving playlist info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving playlist info")

class EmbedCodeResponse(BaseModel):
    embed_code: str

@app.get("/embed-playlist/{playlist_id}", response_model=EmbedCodeResponse)
def embed_playlist(playlist_id: str):
    if not playlist_id:
        raise HTTPException(status_code=400, detail="Playlist ID is required.")
    
    embed_code = (
        f'<iframe width="560" height="315" '
        f'src="https://www.youtube.com/embed/videoseries?list={playlist_id}" '
        f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
        f'allowfullscreen></iframe>'
    )
    return EmbedCodeResponse(embed_code=embed_code)

@app.get("/play-playlist/{playlist_id}")
def play_playlist(playlist_id: str, start_time: str = "00:00"):
    if not playlist_id:
        raise HTTPException(status_code=400, detail="Playlist ID is required.")
    
    response = api.get_playlist_items(playlist_id=playlist_id)
    if response.items:
        first_video_id = response.items[0].content_details.video_id
        
        netherlands_tz = pytz.timezone('Europe/Amsterdam')
        current_time = datetime.now(netherlands_tz)
        
        try:
            desired_time = datetime.strptime(start_time, "%H:%M").replace(year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=netherlands_tz)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM.")
        
        total_seconds = int((desired_time - current_time).total_seconds())
        
        if total_seconds < 0:
            desired_time += timedelta(days=1)
            total_seconds = int((desired_time - current_time).total_seconds())
        
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        webbrowser.open(playlist_url)
        
        video_url = f"https://www.youtube.com/watch?v={first_video_id}&t={total_seconds}s"
        webbrowser.open(video_url)
        
        return {"message": f"Opening playlist and the first video at {start_time} in your default browser."}
    else:
        logging.warning(f"No videos found for playlist ID: {playlist_id}")
        raise HTTPException(status_code=404, detail="No videos found in the playlist.")
