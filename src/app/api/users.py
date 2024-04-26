from fastapi import HTTPException, Depends, status, Request

from app.config import get_settings, log
from app.api.models import UserInDB, UserReg
from app.api import encrypt, crud
#
# from fastapi.security import OAuth2PasswordBearer
from app.api.utils import OAuth2PasswordBearerWithCookie

from email_validator import validate_email, EmailNotValidError
from app.send_email import send_email_async

# from jose import JWTError, jwt
import jwt

from typing import Any, Union
from datetime import datetime, timedelta

# add OAuth2, declaring the url to get user auth tokens:
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scheme_name="JWT")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token", scheme_name="JWT")



# -------------------------------------------------------------------------------------
async def get_user(username: str) -> UserInDB:
    # log.info(f"get_user: looking for {username}")
    user = await crud.get_user_by_name(username)
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
    user = await crud.get_user_by_email(email)
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
    # encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    encoded_jwt = jwt.encode(payload=to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt

# -------------------------------------------------------------------------------------
def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    
    settings = get_settings() # application config settings
    
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    # encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_REFRESH_KEY, settings.JWT_ALGORITHM)
    encoded_jwt = jwt.encode(payload=to_encode, key=settings.JWT_SECRET_REFRESH_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt




# -------------------------------------------------------------------------------------
def user_has_role( user: UserInDB, role: str) -> bool:
    if not user:
        return False
    roles_list = user.roles.split(' ')  # Split the roles string into a list
    return role in roles_list


# -------------------------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = ''
    try:
        settings = get_settings() # application config settings
        # payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
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
        
    except jwt.exceptions.InvalidTokenError as e:
        log.info(f"get_current_user: jwt error: " + repr(e))
    except Exception as e:
        log.info("get_current_user: WARNING NORMAL EXCEPTION CAUGHT")
        log.info(repr(e))
        
    """ except JWTError:
        log.info(f"get_current_user: JWTError")
        raise credentials_exception """
    
    user = await get_user(username) 
    if user is None:
        log.info("get_current_user: user is None!")
        raise credentials_exception
    return user


# -------------------------------------------------------------------------------------
async def get_refresh_user(request: Request) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        cookies = request.cookies # json.loads(request.cookies)
        settings = get_settings() # application config settings
        
        # payload = jwt.decode(cookies['refresh_token'], settings.JWT_SECRET_REFRESH_KEY, algorithms=[settings.JWT_ALGORITHM]) 
        payload = jwt.decode(jwt=cookies['refresh_token'], key=settings.JWT_SECRET_REFRESH_KEY, algorithms=[settings.JWT_ALGORITHM])
        
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
            

    except jwt.exceptions.InvalidTokenError as e:
        log.info(f"get_refresh_user: jwt error: " + repr(e))
    except Exception as e:
        log.info("get_refresh_user: WARNING NORMAL EXCEPTION CAUGHT")
        log.info(repr(e))
            
    """ except JWTError:
        raise credentials_exception """
    
    user = await get_user(username=username) # token_data.username)
    if user is None:
        raise credentials_exception
    return user


# -------------------------------------------------------------------------------------
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if user_has_role(current_user, 'disabled'):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user




# -------------------------------------------------------------------------------------
async def validate_email_address(email: str):
    try:
        validation = validate_email( email, check_deliverability=True)
        # get Unicode normalized version of email address:
        email = validation.email
        
    except EmailNotValidError as e:
        return { "success": False, "msg": str(e) }
        
    return { "success": True, "msg": email }

# -------------------------------------------------------------------------------------
async def validate_new_user_info(user: UserReg):
    
    existingUser = await get_user(user.username)
    if existingUser:
        return { "success": False, 
                 "status_code": status.HTTP_409_CONFLICT, 
                 "msg": "Username already in use."
               }
    
    ret = await validate_email_address(user.email)
    if ret['success']:
        user.email = ret['msg']
    else:
        return { "success": False, 
                 "status_code": status.HTTP_406_NOT_ACCEPTABLE, 
                 "msg": ret['msg']
               }
    
    existingUser = await get_user_by_email(user.email)
    if existingUser:
        return { "success": False, 
                 "status_code": status.HTTP_409_CONFLICT, 
                 "msg": "Email already in use."
               }
    
    return { "success": True, 
             "status_code": status.HTTP_200_OK, 
             "msg": user.email 
           }
    
    
# -------------------------------------------------------------------------------------
async def send_email_validation_email(username: str, email: str, verify_code: str):
    
    body = r'''<p>Hello {name}</p>
<p>Here is your email verification code:<\p>
<p>{code}<\p>
<p>You will be asked to enter this code upon your next login. 
Email verification enables posting and account changes.</p>
<p>-Blake Senftner</p>'''
    body = body.format(name=username, code=verify_code)

    params = { 'msg': { 'subject': 'Verification email',
                        'body': body }
             }
    # print(json.dumps(params, indent = 4))
    
    await send_email_async(email, params, 'verify_email.html')
    
       
# -------------------------------------------------------------------------------------
async def send_password_changed_email(username: str, email: str, new_password: str):
    
    body = r'''<p>Hello {name}</p>
<p>Your username at my website is:<\p>
<p>{name}<\p>
<p>Your password has recently changed and is now:<\p>
<p>{password}<\p>
<p>Use these to login to my Blog. Note, this email is the only location this password is plaintext.</p>
<p>-Blake Senftner</p>'''
    body = body.format(name=username, password=new_password)

    params = { 'msg': { 'subject': 'Password changed email',
                        'body': body }
    }
    # print(json.dumps(params, indent = 4))
    await send_email_async(email, params, 'verify_email.html')
