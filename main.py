import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyyoutube import Api
from dotenv import load_dotenv
import webbrowser
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

app = FastAPI()
logging.basicConfig(level=logging.INFO)

api_key = os.getenv("YOUTUBE_API_KEY")
if not api_key:
    logging.error("YOUTUBE_API_KEY environment variable is not set.")
    raise RuntimeError("YOUTUBE_API_KEY environment variable is required.")

api = Api(api_key=api_key)
scheduler = BackgroundScheduler()

def open_first_video(playlist_id):
    response = api.get_playlist_items(playlist_id=playlist_id)
    if response.items:
        first_video_id = response.items[0].contentDetails.videoId
        video_url = f"https://www.youtube.com/watch?v={first_video_id}"
        webbrowser.open(video_url)
    else:
        logging.warning(f"No videos found for playlist ID: {playlist_id}")

@app.post("/schedule-playlist/")
def schedule_playlist(playlist_id: str, start_time: str):
    netherlands_tz = pytz.timezone('Europe/Amsterdam')
    current_time = datetime.now(netherlands_tz)
    desired_time = datetime.strptime(start_time, "%H:%M").replace(
        year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=netherlands_tz
    )

    if desired_time < current_time:
        desired_time += timedelta(days=1)

    cron_time = CronTrigger(hour=desired_time.hour, minute=desired_time.minute, timezone="Europe/Amsterdam")
    scheduler.add_job(
        open_first_video,
        cron_time,
        args=[playlist_id],
        id=f"youtube_playlist_job_{playlist_id}"
    )
    scheduler.start()
    return {"message": f"Scheduled the first video of playlist {playlist_id} to open at {start_time}."}

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
    logging.info("Scheduler stopped.")
