from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
import aiofiles

from app import config
from app.api.users import get_current_active_user, user_has_role
from app.api.models import UserInDB

from app.config import log

router = APIRouter()

# ------------------------------------------------------------------------------------------------------------------
# endpoint for uploads, restricted to admin accounts
@router.post("/upload", status_code=200)
async def upload(file: UploadFile = File(...), 
                 current_user: UserInDB = Depends(get_current_active_user)):
    
    log.info(f"upload: here!")
    
    if not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized to create Blog Posts")
        
    try:
        upload_path = config.get_base_path() / 'static/uploads' / file.filename
        #
        log.info(f"upload: attempting {upload_path}")
        #
        async with aiofiles.open(upload_path, 'wb') as f:
            CHUNK_SIZE = 1024*1024
            while contents := await file.read(CHUNK_SIZE):
                await f.write(contents)
                
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        await file.close()

    return {"message": f"Successfully uploaded {file.filename}"}