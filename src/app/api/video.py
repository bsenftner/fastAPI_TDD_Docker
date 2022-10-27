from fastapi import APIRouter, Header, Response
from pathlib import Path

# create a local router for paths created in this file
router = APIRouter()

BASE_PATH = Path(__file__).resolve().parent.parent
CHUNK_SIZE = 1024*1024

# ------------------------------------------------------------------------------------------------------------------
# endpoint to play video files located inside the "app/static/video" directory
@router.get("/{video_file}", status_code=200) # , include_in_schema=False) 
async def video_endpoint(video_file: str, range: str = Header(None)):
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    video_path = BASE_PATH / 'static/video' / video_file
    print(f"video path is {video_path}")
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")
