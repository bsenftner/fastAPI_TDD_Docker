from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from passlib.context import CryptContext
from app.config import settings 
from app.api.models import Token, User, UserInDB, UserPublic, UserReg
from app.db import users, database

from fastapi.security import OAuth2PasswordRequestForm
#
# from fastapi.security import OAuth2PasswordBearer
from app.api.utils import OAuth2PasswordBearerWithCookie

from jose import JWTError, jwt
from typing import Any, Union
from datetime import datetime, timedelta
from pydantic import EmailStr

SECRET_KEY = settings.JWT_SECRET_KEY
REFRESH_KEY = settings.JWT_SECRET_REFRESH_KEY
ALGORITHM = settings.JWT_ALGORITHM 
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRES_MINUTES 
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRES_MINUTES 


# for authentication:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)


# add OAuth2, declaring the url to get user auth tokens:
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scheme_name="JWT")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token", scheme_name="JWT")


# create a local API router for the endpoints created in this file:
router = APIRouter()



# -------------------------------------------------------------------------------------
async def get_user(username: str):
    query = users.select().where(users.c.username == username)
    user = await database.fetch_one(query)
    if not user:
        print(f"get_user: no such user")
        return False
    # username = user["username"]
    # print(f'get_user: user = {username}')
    return UserInDB(username=user["username"], 
                    id=user["id"], 
                    hashed_password=user["hashed_password"],
                    email=user["email"],
                    roles=user["roles"])

# -------------------------------------------------------------------------------------
async def get_user_by_email(email: str):
    query = users.select().where(users.c.email == email)
    user = await database.fetch_one(query)
    if not user:
        print(f"get_user_by_email: no such user")
        return False
    return UserInDB(username=user["username"], 
                    id=user["id"], 
                    hashed_password=user["hashed_password"],
                    email=user["email"],
                    roles=user["roles"])


# -------------------------------------------------------------------------------------
async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# -------------------------------------------------------------------------------------
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt

# -------------------------------------------------------------------------------------
def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, REFRESH_KEY, ALGORITHM)
    return encoded_jwt



# -------------------------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        # print(f"get_current_user: username is {username}")
        expTime: str = payload.get("exp")
        # print(f"get_current_user: exp is {expTime}")
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
        print("get_current_user: user is None!")
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
        
        payload = jwt.decode(cookies['refresh_token'], REFRESH_KEY, algorithms=[ALGORITHM]) 
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
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# -------------------------------------------------------------------------------------
@router.post("/token", summary="Create access and refresh tokens for user", response_model=Token)
async def login_for_access_token(response: Response, 
                                 form_data: OAuth2PasswordRequestForm = Depends()):

    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(form_data.username)
    
    access_cookie_value = f"Bearer {access_token}"
    
    refresh_token = create_refresh_token(form_data.username)
    
    refresh_cookie_value = refresh_token
    
    # Store refresh and access tokens in cookie
    response.set_cookie('access_token', 
                        access_cookie_value, 
                        ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
                        '/', None, False, True, 'lax')
    response.set_cookie('refresh_token', 
                        refresh_cookie_value,
                        REFRESH_TOKEN_EXPIRE_MINUTES * 60, 
                        REFRESH_TOKEN_EXPIRE_MINUTES * 60, 
                        '/', None, False, True, 'lax')

    # return {"access_token": access_token, "token_type": "bearer"}
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

# --------------------------------------------------------------------------------------------------------------
# Refresh access token
@router.get('/refresh')
async def refresh_token(response: Response, request: Request): 
    try:
        refreshUser = await get_refresh_user(request)
        if not refreshUser:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='The user belonging to this token no logger exist')

        username = refreshUser.username
        access_token = create_access_token(username)
        access_cookie_value = 'Bearer ' + access_token

        # Store refresh and access tokens in cookie
        response.set_cookie('access_token', 
                        access_cookie_value, 
                        ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
                        '/', None, False, True, 'lax')
    
    except Exception as e:
        error = e.__class__.__name__
        if error == 'MissingTokenError':
            raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail='Please provide refresh token')
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=error)
        
    return {'access_token': access_token}


# --------------------------------------------------------------------------------------------------------------
# return info about the current logged in user:
@router.get("/users/me", response_model=UserPublic)
async def read_users_me(request: Request, current_user: User = Depends(get_current_active_user)):
    # print(request.cookies)
    return {"username": current_user.username, 
            "id": current_user.id, 
            "email": current_user.email, 
            "roles": current_user.roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/register", response_model=UserPublic)
async def sign_up(user: UserReg):
    existingUser = await get_user(user.username)
    if existingUser:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already in use.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    existingUser = await get_user_by_email(user.email)
    if existingUser:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    hashed_password = get_password_hash(user.password)
    
    emailAddr = ''
    roles = 'user'
    if len(user.email)>0: 
        if user.username=='bsenftner' and user.email=='bsenftner@earthlink.net':
            roles += ' admin'
        emailAddr = EmailStr(user.email)
        
    query = users.insert().values( username=user.username, 
                                   hashed_password=hashed_password,
                                   email=emailAddr,
                                   roles=roles )
    last_record_id = await database.execute(query)
    
    return {"username": user.username, "id": last_record_id, "email": emailAddr, "roles": roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/logout", response_model=UserPublic)
async def logout(response: Response, current_user: User = Depends(get_current_active_user)):
    # print("logout hit!")
    response.set_cookie(key="access_token",value=f"Bearer 0", httponly=True)
    response.set_cookie(key="refresh_token",value=f"0", httponly=True)
    return {"username": current_user.username, "id": current_user.id, "email": current_user.email, "roles": current_user.roles}


