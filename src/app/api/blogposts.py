from fastapi import APIRouter, HTTPException, Path 

from app.api import crud
from app.api.models import BlogPostDB, BlogPostSchema

from typing import List


router = APIRouter()

# ----------------------------------------------------------------------------------------------
# declare a POST endpoint on the root
# this will respond with a BlogPostDB upon succes 
# This will receive a BlogPostSchema within payload 
@router.post("/", response_model=BlogPostDB, status_code=201)
async def create_blogpost(payload: BlogPostSchema):
    blogpost_id = await crud.post_blogpost(payload)

    response_object = {
        "id": blogpost_id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.get("/{id}/", response_model=BlogPostDB)
async def read_blogpost(id: int = Path(..., gt=0),):
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")
    return blogpost

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a BlogPostDB subtype. See import of List top of file. 
@router.get("/", response_model=List[BlogPostDB])
async def read_all_blogposts():
    return await crud.get_all_blogposts()

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.put("/{id}/", response_model=BlogPostDB)
async def update_blogpost(payload: BlogPostSchema, id: int = Path(..., gt=0),):
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogpost_id = await crud.put_blogpost(id, payload)

    response_object = {
        "id": blogpost_id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.delete("/{id}/", response_model=BlogPostDB)
async def delete_blogpost(id: int = Path(..., gt=0)):
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    await crud.delete_blogpost(id)

    return blogpost
