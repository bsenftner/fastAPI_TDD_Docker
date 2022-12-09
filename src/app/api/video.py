from fastapi import APIRouter, Header, Response

from app import config

# create a local router for paths created in this file
router = APIRouter()


# ------------------------------------------------------------------------------------------------------------------
# endpoint to play video files located inside the "app/static/video" directory
@router.get("/{video_file}", status_code=200) 
async def video_endpoint(video_file: str, range: str = Header(None)):
    
    # config.log.info(f"video_file is >{video_file}<")
    # config.log.info(f"range is >{range}<")
    
    start, end = 0, 0
    if range:
        start, end = range.replace("bytes=", "").split("-")
    
    start = int(start)
    
    CHUNK_SIZE = 1024*1024
    end = int(end) if end else start + CHUNK_SIZE
    
    video_path = config.get_base_path() / 'static/uploads' / video_file
    
    # config.log.info(f"video path is {video_path}")
    
    with open(video_path, "rb") as video:
        # config.log.info(f"video opened!")
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")
