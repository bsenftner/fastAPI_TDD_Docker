from fastapi import APIRouter, HTTPException, Depends, status, Response
from passlib.context import CryptContext
from app.db import users, database

from fastapi.security import OAuth2PasswordRequestForm
#
# from fastapi.security import OAuth2PasswordBearer
from app.api.utils import OAuth2PasswordBearerWithCookie

from jose import JWTError, jwt
from typing import Optional
from datetime import datetime, timedelta

from typing import Union
from pydantic import BaseModel, Field

from pathlib import Path
#
ENV_PATH = Path(__file__).resolve().parent.parent
# print(f'users: env_path is {ENV_PATH}')
#
from dotenv import dotenv_values 
envConfig = dotenv_values(str(ENV_PATH / ".env"))  
'''
print('users envConfig is')
for key, value in envConfig.items():
    print(key, ' : ', value)
'''
secret = envConfig["JWT_SECRET"]
print(f'secret is {secret}')

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# pydantic data classes:

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None
    
class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None
    
class UserInDB(User):
    hashed_password: str

class UserIn(User):
    password: str


# for authentication:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# add OAuth2, declaring the url to get user auth tokens:
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")

# create a local API router for the endpoints created in this file:
router = APIRouter()



async def get_user(username: str):
    query = users.select().where(users.c.username == username)
    user = await database.fetch_one(query)
    if not user:
        # print(f"get_user: no such user")
        return False
    # print(f"get_user: user = {user}")
    return UserInDB(username=user["username"], hashed_password=user["hashed_password"])


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        ) 
    response.set_cookie(key="access_token",value=f"Bearer {access_token}", httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user



@router.post("/users/", response_model=User)
async def sign_up(user: UserIn):
    hashed_password = get_password_hash(user.password)
    query = users.insert().values(
        username=user.username, hashed_password=hashed_password
    )
    last_record_id = await database.execute(query)
    return {"username": user.username, "id": last_record_id}


@router.post("/users/logout/", response_model=User)
async def logout(response: Response, current_user: User = Depends(get_current_active_user)):
    print("logout hit!")
    response.set_cookie(key="access_token",value=f"Bearer 0", httponly=True)
    return current_user

