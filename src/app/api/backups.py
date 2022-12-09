from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

import glob
from typing import List
from pathlib import Path

from app import config
from app.api.users import get_current_active_user, user_has_role
from app.api.models import UserInDB

from app.config import log

router = APIRouter()

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a str subtype. See import of List top of file. 
@router.get("/", response_model=List[str])
async def read_all_backups(current_user: UserInDB = Depends(get_current_active_user)) -> List[str]:
    
    log.info(f"read_all_backups: here!")
    
    if not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized")
    
    backups_path = config.get_base_path() / 'backups/*.gz' 
    
    log.info(f"read_all_backups: backups_path {backups_path}")
    
    result = []
    result.extend(glob.glob(str(backups_path)))
    
    ret = []
    for longPath in result:
        parts = longPath.split('/')
        count = len(parts)
        ret.append( parts[count-1] )
        
    log.info(f"read_all_backups: got {ret}")
    
    return ret

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a str subtype. See import of List top of file. 
@router.get("/{expected_filename}", status_code=200)  
async def read_backup(expected_filename: str, current_user: UserInDB = Depends(get_current_active_user)):
    
    log.info(f"read_backup: here!")
    
    if not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized")
    
    backup_path = config.get_base_path() / 'backups' /  expected_filename
    
    log.info(f"read_backup: backup_path {backup_path}")
    
    backup_info = Path(backup_path)
    if not backup_info.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="File Not Found")
        
    return FileResponse(backup_path)
