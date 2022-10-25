# ---------------------------------------------------------------------------------------------
# This file contains the JSON endpoints for notes, handling the CRUD operations with the db 
#
from fastapi import APIRouter, HTTPException, Path, Depends, status
import json
from typing import List

from app.api import crud
from app.api.models import NoteDB, NoteSchema
from app.api.users import User, get_current_active_user, user_has_role



router = APIRouter()

# ----------------------------------------------------------------------------------------------
# declare a POST endpoint on the root
# this will respond with a NoteDB upon success 
# This will receive a NoteSchema within payload 
@router.post("/", response_model=NoteDB, status_code=201)
async def create_note(payload: NoteSchema, 
                      current_user: User = Depends(get_current_active_user)):
    
    # ensure data is valid json:
    try:
        jsonDict = json.load(payload.data)
    except ValueError as e:
        error = e.__class__.__name__
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=error)
   
    # I'm forcing all note titles to be unique:
    note = await crud.get_note_by_title(payload.title)
    if note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    note_id = await crud.post_note(payload, current_user.id)

    response_object = {
        "id": note_id,
        "owner": current_user.id,
        "title": payload.title,
        "description": payload.description,
        "data": payload.data,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# get note, with protection: only works for owner and admins
# Note: id's type is validated as greater than 0
@router.get("/{id}/", response_model=NoteDB)
async def read_note(id: int = Path(..., gt=0),
                    current_user: User = Depends(get_current_active_user)):
    
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    if user_has_role( current_user, "admin") or current_user.id == note.owner:
        return note
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                        detail="Not Authorized to access other's notes")

# ----------------------------------------------------------------------------------------------
# return list of notes, only works for admin
# The response_model is a List with a NoteDB subtype. See import of List top of file. 
@router.get("/", response_model=List[NoteDB])
async def read_all_notes(current_user: User = Depends(get_current_active_user)):
    if user_has_role( current_user, "admin"):
        return await crud.get_all_notes()
    
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized to access all notes")

# ----------------------------------------------------------------------------------------------
# update a note, with protection: only works for owner and admins
# Note: id's type is validated as greater than 0  
# data is also tested for being valid json
@router.put("/{id}/", response_model=NoteDB)
async def update_note(payload: NoteSchema, id: int = Path(..., gt=0), 
                      current_user: User = Depends(get_current_active_user)):
    
    # print(f"Notes:PUT:: payload is {payload.data}!")
    # print(type(payload.data))
    
    # ensure data is valid json:
    try:
        jsonDict = json.loads(payload.data)
    except ValueError as e:
        error = e.__class__.__name__
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.owner != current_user.id and not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized to change other's notes")
        
    note_id = await crud.put_note(id, payload, note.owner)

    response_object = {
        "id": note_id,
        "owner": note.owner,
        "title": payload.title,
        "description": payload.description,
        "data": payload.data,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# delete a note, with protection: only works for owner and admins
# Note: id's type is validated as greater than 0  
@router.delete("/{id}/", response_model=NoteDB)
async def delete_note(id: int = Path(..., gt=0), 
                      current_user: User = Depends(get_current_active_user)):
    
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.owner != current_user.id and not user_has_role(current_user,"admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not Authorized to delete other's notes")
        
    await crud.delete_note(id)

    return note
