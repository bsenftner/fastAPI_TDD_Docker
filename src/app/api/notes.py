from fastapi import APIRouter, HTTPException, Path 

from app.api import crud
from app.api.models import NoteDB, NoteSchema

from typing import List


router = APIRouter()

# ----------------------------------------------------------------------------------------------
# declare a POST endpoint on the root
# this will respond with a NoteDB upon succes 
# This will receive a NoteSchema within payload 
@router.post("/", response_model=NoteDB, status_code=201)
async def create_note(payload: NoteSchema):
    note_id = await crud.post_note(payload)

    response_object = {
        "id": note_id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.get("/{id}/", response_model=NoteDB)
async def read_note(id: int = Path(..., gt=0),):
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a NoteDB subtype. See import of List top of file. 
@router.get("/", response_model=List[NoteDB])
async def read_all_notes():
    return await crud.get_all_notes()

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.put("/{id}/", response_model=NoteDB)
async def update_note(payload: NoteSchema, id: int = Path(..., gt=0),):
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note_id = await crud.put_note(id, payload)

    response_object = {
        "id": note_id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.delete("/{id}/", response_model=NoteDB)
async def delete_note(id: int = Path(..., gt=0)):
    note = await crud.get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await crud.delete_note(id)

    return note
