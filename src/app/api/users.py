from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from passlib.context import CryptContext
from app.config import settings 
from app.api.models import Token, User, UserInDB, UserPublic, UserReg, basicTextPayload
from app.db import users, database

from fastapi.security import OAuth2PasswordRequestForm
#
# from fastapi.security import OAuth2PasswordBearer
from app.api.utils import OAuth2PasswordBearerWithCookie

from jose import JWTError, jwt
from typing import Any, Union
from datetime import datetime, timedelta
from pydantic import EmailStr

import secrets
import string
from app.send_email import send_email_async
# import json

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


'''
    print(f'get_user: user = {username}')
    print(f'get_user: id = {id}')
    print(f'get_user: verify_code = {verify_code}')
    print(f'get_user: ushashed_passworder = {hashed_password}')
    print(f'get_user: email = {email}')
    print(f'get_user: roles = {roles}')
''' 
# -------------------------------------------------------------------------------------
async def get_user(username: str):
    # print(f"get_user: looking for {username}")
    
    query = users.select().where(users.c.username == username)
    user = await database.fetch_one(query)
    if not user:
        print(f"get_user: no such user")
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
async def get_user_by_email(email: str):
    query = users.select().where(users.c.email == email)
    user = await database.fetch_one(query)
    if not user:
        print(f"get_user_by_email: no such user")
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
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if user_has_role(current_user, 'disabled'):
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
@router.get('/refresh', summary="Submit refresh token and get new access token")
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
@router.get("/users/me", summary="Get current logged in user data", response_model=UserPublic)
async def read_users_me(request: Request, current_user: User = Depends(get_current_active_user)):
    # print(request.cookies)
    return {"username": current_user.username, 
            "id": current_user.id, 
            "email": current_user.email, 
            "roles": current_user.roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/register", summary="Register new user", response_model=UserPublic)
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
    
    emailAddr = ''
    roles = 'user unverified'
    if len(user.email)>0: 
        if user.username=='bsenftner' and user.email=='bsenftner@earthlink.net':
            roles += ' admin'
        emailAddr = EmailStr(user.email)
    else:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Email must be a valid address.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    hashed_password = get_password_hash(user.password)
    
    verify_code = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    # print(f'email verification code is {verify_code}')
        
    # validation of user info complete, create the user in the db:
    query = users.insert().values( username=user.username, 
                                   hashed_password=hashed_password,
                                   verify_code=verify_code,
                                   email=emailAddr,
                                   roles=roles )
    last_record_id = await database.execute(query)
    
    body = '''\
<p>Hello {name}</p>
<p>Here is your email verification code:<\p>
<p>{code}<\p>
<p>You will be asked to enter this code upon your next login. Email verification enables posting and account changes.</p>
<p>-Blake Senftner</p>\
'''
    body = body.format(name=user.username, code=verify_code)

    params = { 'msg': { 'subject': 'Verification email',
                        'body': body }
    }
    # print(json.dumps(params, indent = 4))
    await send_email_async(user.email, params, 'verify_email.html')
    
    return {"username": user.username, "id": last_record_id, "email": emailAddr, "roles": roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/logout", summary="Logout current user", response_model=UserPublic)
async def logout(response: Response, current_user: User = Depends(get_current_active_user)):
    # print("logout hit!")
    response.set_cookie(key="access_token",value=f"Bearer 0", httponly=True)
    response.set_cookie(key="refresh_token",value=f"0", httponly=True)
    return {"username": current_user.username, "id": current_user.id, "email": current_user.email, "roles": current_user.roles}


# -------------------------------------------------------------------------------------
@router.post("/users/verify", summary="Accept user email verification code")
async def verify_user_email(payload: basicTextPayload, current_user: UserInDB = Depends(get_current_active_user)):

    ret = 'ok'
    
    if user_has_role( current_user, 'unverified'):
        # print(f"current_user vcode {current_user.verify_code} and payload vcode {payload.code}")
        if current_user.verify_code != payload.code:
            raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="The verification code does not match.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        else:
            role_list = current_user.roles.split()
            current_user.roles = ''
            first = True
            for role in role_list:
                if role != 'unverified':
                    if not first:
                        current_user.roles += ' '
                    current_user.roles += role
                    first = False
            query = (
                users
                .update()
                .where(current_user.id == users.c.id)
                .values(roles=current_user.roles)
                .returning(users.c.id)
            )
            ret = await database.execute(query)
            if ret != current_user.id:
                ret = 'ERROR!'
            
    return { 'status': 'ok' }


# -------------------------------------------------------------------------------------
@router.post("/users/resetpass", summary="Reset password and send user email with new password")
async def reset_user_password(payload: basicTextPayload):

    existingUser = await get_user(payload.text)
    if not existingUser:
        existingUser = await get_user_by_email(payload.text)
        if not existingUser:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with that username or email found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            print('existing user was email')
    else:
        print('existing user was username')
    
    if user_has_role( existingUser, 'unverified'):
        if existingUser.verify_code != payload.code:
            raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="The requested account must have a verified email to receive reset passwords.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    reset_password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    print(f'reset_password is {reset_password}')
    
    hashed_password = get_password_hash(reset_password)
    
    query = users.update().values( username=existingUser.username, 
                                   hashed_password=hashed_password,
                                   verify_code=existingUser.verify_code,
                                   email=existingUser.email,
                                   roles=existingUser.roles ).returning(users.c.id)
    id = await database.execute(query=query)
    if id!=existingUser.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    body = '''\
<p>Hello {name}</p>
<p>Your username at my website is:<\p>
<p>{name}<\p>
<p>Your reset password is:<\p>
<p>{password}<\p>
<p>Use these to login to my Blog. Note, this email is the only location this password is plaintext.</p>
<p>-Blake Senftner</p>\
'''
    body = body.format(name=existingUser.username, password=reset_password)

    params = { 'msg': { 'subject': 'Password reset email',
                        'body': body }
    }
    # print(json.dumps(params, indent = 4))
    await send_email_async(existingUser.email, params, 'verify_email.html')
    
    return { 'status': 'ok' }


# -------------------------------------------------------------------------------------
@router.post("/users/setpass", summary="Set user password and send user email with new password")
async def set_user_password(payload: basicTextPayload, current_user: UserInDB = Depends(get_current_active_user)):
    
    if user_has_role( current_user, 'unverified'):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Account must have a verified email to accept account changes.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_password = payload.text
    print(f'set_user_password: new password is {new_password}')
    
    hashed_password = get_password_hash(new_password)
    
    query = users.update().values( username=current_user.username, 
                                   hashed_password=hashed_password,
                                   verify_code=current_user.verify_code,
                                   email=current_user.email,
                                   roles=current_user.roles ).returning(users.c.id)
    id = await database.execute(query=query)
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    body = '''\
<p>Hello {name}</p>
<p>Your username at my website is:<\p>
<p>{name}<\p>
<p>Your password changed and is now:<\p>
<p>{password}<\p>
<p>Use these to login to my Blog. Note, this email is the only location this password is plaintext.</p>
<p>-Blake Senftner</p>\
'''
    body = body.format(name=current_user.username, password=new_password)

    params = { 'msg': { 'subject': 'Password changed email',
                        'body': body }
    }
    # print(json.dumps(params, indent = 4))
    await send_email_async(current_user.email, params, 'verify_email.html')
    
    return { 'status': 'ok' }

# -------------------------------------------------------------------------------------
@router.post("/users/setemail", summary="Set user email and send email verification code to that account.")
async def set_user_email(payload: basicTextPayload, current_user: UserInDB = Depends(get_current_active_user)):
    
    if user_has_role( current_user, 'unverified'):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Account must have a verified email to accept account changes.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    new_email = payload.text
    if new_email == current_user.email:
        print('set_user_email: same email address, no change necessary.')
        return { 'status': 'ok' }
    
    
    verify_code = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    
    new_roles = current_user.roles + ' unverified'
    username = current_user.username
    print(f'set_user_email: new email is {new_email} for user {username} with roles after this action of {new_roles}')
    print(f'set_user_email: new email verify code {verify_code}')
    
    query = users.update().values( username=username, 
                                   hashed_password=current_user.hashed_password,
                                   verify_code=verify_code,
                                   email=new_email,
                                   roles=new_roles
                                 ).returning(users.c.id)
    
    id = await database.execute(query=query)
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    body = '''\
<p>Hello {name}</p>
<p>Here is your email verification code:<\p>
<p>{code}<\p>
<p>You will be asked to enter this code upon your next login. Email verification enables posting and account changes.</p>
<p>-Blake Senftner</p>\
'''
    body = body.format(name=current_user.username, code=verify_code)

    params = { 'msg': { 'subject': 'Verification email',
                        'body': body }
    }
    # print(json.dumps(params, indent = 4))
    await send_email_async(new_email, params, 'verify_email.html')
    
    return { 'status': 'ok' }


# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.delete("/users/disable", response_model=UserPublic, summary="Disable the current user account.")
async def delete_user(current_user: UserInDB = Depends(get_current_active_user)):
    
    new_roles = current_user.roles + " disabled"
    
    query = users.update().values( username=current_user.username, 
                                   hashed_password=current_user.hashed_password,
                                   verify_code=current_user.verify_code,
                                   email=current_user.email,
                                   roles=new_roles
                                 ).returning(users.c.id)
    id = await database.execute(query=query)
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_user.roles = new_roles
    
    return  {"username": current_user.username, 
             "id": current_user.id, 
             "email": current_user.email, 
             "roles": current_user.roles}
