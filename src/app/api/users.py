from fastapi import HTTPException, Depends, status, Request

from app.config import get_settings, log
from app.api.models import UserInDB
from app.db import users_tb, database
from app.api import encrypt 
#
# from fastapi.security import OAuth2PasswordBearer
from app.api.utils import OAuth2PasswordBearerWithCookie

from jose import JWTError, jwt
from typing import Any, Union
from datetime import datetime, timedelta

# add OAuth2, declaring the url to get user auth tokens:
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scheme_name="JWT")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token", scheme_name="JWT")



# -------------------------------------------------------------------------------------
async def get_user(username: str) -> UserInDB:
    # log.info(f"get_user: looking for {username}")
    
    query = users_tb.select().where(users_tb.c.username == username)
    user = await database.fetch_one(query)
    if not user:
        log.info(f"get_user: no such user")
        return False
    
    username = user['username']
    id = user['id']
    verify_code = user["verify_code"]
    hashed_password = user["hashed_password"]
    email = user["email"]
    roles = user["roles"]

    return UserInDB(username=user["username"], 
                    id=id, 
                    verify_code=verify_code,
                    hashed_password=hashed_password,
                    email=email,
                    roles=roles)

# -------------------------------------------------------------------------------------
async def get_user_by_email(email: str) -> UserInDB:
    query = users_tb.select().where(users_tb.c.email == email)
    user = await database.fetch_one(query)
    if not user:
        log.info(f"get_user_by_email: no such user")
        return False
    return UserInDB(username=user["username"], 
                    id=user["id"], 
                    verify_code=user['verify_code'],
                    hashed_password=user["hashed_password"],
                    email=user["email"],
                    roles=user["roles"])


# -------------------------------------------------------------------------------------
async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not encrypt.verify_password(password, user.hashed_password):
        return False
    return user


# -------------------------------------------------------------------------------------
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    
    settings = get_settings() # application config settings
    
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    return encoded_jwt

# -------------------------------------------------------------------------------------
def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    
    settings = get_settings() # application config settings
    
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_REFRESH_KEY, settings.JWT_ALGORITHM)
    return encoded_jwt




# -------------------------------------------------------------------------------------
def user_has_role( user: UserInDB, role: str):
    return role in user.roles


# -------------------------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        settings = get_settings() # application config settings
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        # log.info(f"get_current_user: username is {username}")
        expTime: str = payload.get("exp")
        # log.info(f"get_current_user: exp is {expTime}")
        if username is None:
            raise credentials_exception
        if expTime is None:
            raise credentials_exception
        
        if datetime.fromtimestamp(expTime) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    except JWTError:
        raise credentials_exception
    
    user = await get_user(username) # token_data.username)
    if user is None:
        log.info("get_current_user: user is None!")
        raise credentials_exception
    return user


# -------------------------------------------------------------------------------------
async def get_refresh_user(request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        cookies = request.cookies # json.loads(request.cookies)
        settings = get_settings() # application config settings
        payload = jwt.decode(cookies['refresh_token'], settings.JWT_SECRET_REFRESH_KEY, algorithms=[settings.JWT_ALGORITHM]) 
        username: str = payload.get("sub")
        expTime: str = payload.get("exp")
        if username is None:
            raise credentials_exception
        if expTime is None:
            raise credentials_exception
        
        if datetime.fromtimestamp(expTime) < datetime.now():
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            

    except JWTError:
        raise credentials_exception
    
    user = await get_user(username=username) # token_data.username)
    if user is None:
        raise credentials_exception
    return user


# -------------------------------------------------------------------------------------
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if user_has_role(current_user, 'disabled'):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

