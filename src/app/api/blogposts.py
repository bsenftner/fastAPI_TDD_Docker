# ----------------------------------------------------------------------------------------------
# This file contains the JSON endpoints for blog posts, handling the CRUD operations with the db 
#
from fastapi import APIRouter, HTTPException, Path, Depends, status

from app.api import crud
from app.api.users import User, get_current_active_user
from app.api.models import BlogPostDB, BlogPostSchema

from typing import List


router = APIRouter()

# ----------------------------------------------------------------------------------------------
# declare a POST endpoint on the root 
@router.post("/", response_model=BlogPostDB, status_code=201)
async def create_blogpost(payload: BlogPostSchema, 
                          current_user: User = Depends(get_current_active_user)) -> dict:
    
    blogpost_id = await crud.post_blogpost(payload, current_user.id)

    response_object = {
        "id": blogpost_id,
        "owner": current_user.id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.get("/{id}/", response_model=BlogPostDB)
async def read_blogpost(id: int = Path(..., gt=0),) -> dict:
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")
    return blogpost

# ----------------------------------------------------------------------------------------------
# The response_model is a List with a BlogPostDB subtype. See import of List top of file. 
@router.get("/", response_model=List[BlogPostDB])
async def read_all_blogposts() -> dict:
    return await crud.get_all_blogposts()

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.put("/{id}/", response_model=BlogPostDB)
async def update_blogpost(payload: BlogPostSchema, id: int = Path(..., gt=0), 
                          current_user: User = Depends(get_current_active_user)) -> dict:
    
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    if blogpost.owner != current_user.id:
        HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                      detail='You are not the owner of this BlogPost')
        
    blogpost_id = await crud.put_blogpost(id, payload)

    response_object = {
        "id": blogpost_id,
        "owner": current_user.id,
        "title": payload.title,
        "description": payload.description,
    }
    return response_object

# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.delete("/{id}/", response_model=BlogPostDB)
async def delete_blogpost(id: int = Path(..., gt=0), 
                          current_user: User = Depends(get_current_active_user)) -> dict:
    blogpost = await crud.get_blogpost(id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    await crud.delete_blogpost(id)

    return blogpost
