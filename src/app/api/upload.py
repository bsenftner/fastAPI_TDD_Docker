from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
import aiofiles

import glob
from typing import List

from app import config
from app.api.users import get_current_active_user, user_has_role
from app.api.models import UserInDB

from app.config import log

router = APIRouter()

# ------------------------------------------------------------------------------------------------------------------
# endpoint for uploads, restricted to admin accounts
@router.post("/", status_code=200)
async def upload(file: UploadFile = File(...), 
                 current_user: UserInDB = Depends(get_current_active_user)):
    
    if not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized to upload files")
        
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

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a str subtype. See import of List top of file. 
@router.get("/", response_model=List[str])
async def read_all_uploads(current_user: UserInDB = Depends(get_current_active_user)) -> List[str]:
    
    # log.info(f"read_all_uploads: here!")
    
    if not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized")
    
    upload_path = config.get_base_path() / 'static/uploads/*' 
    
    # log.info(f"read_all_uploads: upload_path {upload_path}")
    
    # result = await glob.glob(upload_path)
    
    result = []
    result.extend(glob.glob(str(upload_path)))
    
    ret = []
    for longPath in result:
        parts = longPath.split('/')
        count = len(parts)
        ret.append( parts[count-1] )
        
    log.info(f"read_all_uploads: got {ret}")
    
    return ret