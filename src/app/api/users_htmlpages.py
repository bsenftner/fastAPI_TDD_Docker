
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from app.api.models import Token, UserInDB, UserPublic, UserReg, basicTextPayload
from app.api import encrypt 

from fastapi.security import OAuth2PasswordRequestForm

import secrets
import string

from pydantic import EmailStr

from app.config import get_settings, log 
from app.api import crud, users 
from app.api.users import validate_new_user_info

# create a local API router for the endpoints created in this file:
router = APIRouter()



# -------------------------------------------------------------------------------------
@router.post("/token", summary="Create access and refresh tokens for user", response_model=Token)
async def login_for_access_token(response: Response, 
                                 form_data: OAuth2PasswordRequestForm = Depends()):

    user = await users.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = users.create_access_token(form_data.username)
    
    access_cookie_value = f"Bearer {access_token}"
    
    refresh_token = users.create_refresh_token(form_data.username)
    
    refresh_cookie_value = refresh_token
    
    settings = get_settings() # application config settings
    
    # Store refresh and access tokens in cookie
    response.set_cookie('access_token', 
                        access_cookie_value, 
                        settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60,
                        settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60, 
                        '/', None, False, True, 'lax')
    response.set_cookie('refresh_token', 
                        refresh_cookie_value,
                        settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60, 
                        settings.REFRESH_TOKEN_EXPIRES_MINUTES * 60, 
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
        refreshUser = await users.get_refresh_user(request)
        if not refreshUser:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='The user belonging to this token no logger exist')

        username = refreshUser.username
        access_token = users.create_access_token(username)
        access_cookie_value = 'Bearer ' + access_token

        settings = get_settings() # application config settings
        
        # Store refresh and access tokens in cookie
        response.set_cookie('access_token', 
                        access_cookie_value, 
                        settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60,
                        settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60, 
                        '/', None, False, True, 'lax')
    
    except Exception as e:
        error = e.__class__.__name__
        if error == 'MissingTokenError':
            raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail='Please provide refresh token')
        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=error)
        
    return {'access_token': access_token}


# --------------------------------------------------------------------------------------------------------------
# return info about the current logged in user:
@router.get("/users/me", 
            status_code=status.HTTP_200_OK, 
            summary="Get current logged in user data", 
            response_model=UserPublic)
async def read_users_me(request: Request, current_user: UserInDB = Depends(users.get_current_active_user)):
    print(current_user)
    return {"username": current_user.username, 
            "id": current_user.id, 
            "email": current_user.email, 
            "roles": current_user.roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/register",  
             status_code=status.HTTP_201_CREATED, 
             summary="Register new user", 
             response_model=UserPublic)
async def sign_up(user: UserReg):
    
    ret = await validate_new_user_info(user)
    if not ret['success']:
        raise HTTPException( status_code=ret['status_code'], 
                             detail=ret.msg, 
                             headers={"WWW-Authenticate": "Bearer"}, )
    
    # when successful, validate_new_user_info() returns the Unicode normalized email in the msg return field:
    emailAddr = EmailStr(ret['msg'])
    
    settings = get_settings() # application config settings
    
    # basic "roles" setup:
    roles = 'user unverified'
    #
    # in app config the username and email of the admin/superuser is kept:
    if user.username==settings.ADMIN_USERNAME and user.email==settings.ADMIN_EMAIL:
        roles += ' admin'
        
    # we store the hashed password in the db:
    hashed_password = encrypt.get_password_hash(user.password)
    
    # generate an email verification code:
    verify_code = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    # log.info(f'email verification code is {verify_code}')
        
    # validation of user info complete, create the user in the db:
    last_record_id = await crud.post_user( user, hashed_password, verify_code, roles )
    
    await users.send_email_validation_email( user.username, user.email, verify_code )
    
    return {"username": user.username, "id": last_record_id, "email": emailAddr, "roles": roles}


# --------------------------------------------------------------------------------------------------------------
@router.post("/users/logout",  
             status_code=status.HTTP_200_OK, 
             summary="Logout current user", 
             response_model=UserPublic)
async def logout(response: Response, current_user: UserInDB = Depends(users.get_current_active_user)):
    response.set_cookie(key="access_token",value=f"Bearer 0", httponly=True)
    response.set_cookie(key="refresh_token",value=f"0", httponly=True)
    return {"username": current_user.username, 
            "id": current_user.id, 
            "email": current_user.email, 
            "roles": current_user.roles}


# -------------------------------------------------------------------------------------
@router.post("/users/verify",  
             status_code=status.HTTP_200_OK, 
             summary="Accept user email verification code")
async def verify_user_email(payload: basicTextPayload, current_user: UserInDB = Depends(users.get_current_active_user)):

    statusStr = "Already verified"
    
    if users.user_has_role( current_user, 'unverified'):
        log.info(f"current_user vcode {current_user.verify_code} and payload vcode {payload.text}")
        if current_user.verify_code != payload.text:
            raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="The verification code does not match.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        else:
            # from here till the line break is removing 'unverified' from roles: 
            role_list = current_user.roles.split()
            current_user.roles = ''
            first = True
            for role in role_list:
                if role != 'unverified':
                    if not first:
                        current_user.roles += ' '
                    current_user.roles += role
                    first = False
            
            # update user in the database: 
            id = await crud.put_user( current_user.id, current_user )
            if id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database error.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            statusStr = "Ok"
            
    return { 'status': statusStr }


# -------------------------------------------------------------------------------------
# accepts username or a user's email, resets their password and sends email with new password 
# specifically not a protected endpoint. 
@router.post("/users/resetpass",  
             status_code=status.HTTP_200_OK, 
             summary="Reset password and send user email with new password")
async def reset_user_password(payload: basicTextPayload):

    log.info(f"reset_user_password: working with >{payload.text}<")
    
    existingUser = await users.get_user(payload.text)
    if not existingUser:
        existingUser = await users.get_user_by_email(payload.text)
        if not existingUser:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with that username or email found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            log.info('existing user was email')
    else:
        log.info('existing user was username')
    
    if users.user_has_role( existingUser, 'unverified'):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="The requested account must have a verified email to receive reset passwords.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    reset_password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    log.info(f'reset_password is {reset_password}')
    
    existingUser.hashed_password = encrypt.get_password_hash(reset_password)
    
    # update user in the database: 
    id = await crud.put_user( existingUser.id, existingUser )
    if id!=existingUser.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await users.send_password_changed_email(existingUser.username, existingUser.email, reset_password)
    
    return { 'status': 'ok' }


# -------------------------------------------------------------------------------------
@router.post("/users/setpass",  
             status_code=status.HTTP_200_OK, 
             summary="Set user password and send user email with new password")
async def set_user_password( payload: basicTextPayload, 
                             current_user: UserInDB = Depends(users.get_current_active_user)):
    
    if users.user_has_role( current_user, 'unverified'):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Account must have a verified email to accept account changes.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_user.hashed_password = encrypt.get_password_hash(payload.text)
    
    log.info(f'set_user_password: new hashed_password is {current_user.hashed_password}')
    
    # update user in the database: 
    id = await crud.put_user( current_user.id, current_user )
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await users.send_password_changed_email(current_user.username, current_user.email, payload.text)
    
    return { 'status': 'ok' }

# -------------------------------------------------------------------------------------
@router.post("/users/setemail",  
             status_code=status.HTTP_200_OK, 
             summary="Set user email and send email verification code to that account.")
async def set_user_email(payload: basicTextPayload, current_user: UserInDB = Depends(users.get_current_active_user)):
    
    if users.user_has_role( current_user, 'unverified'):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Account must have a verified email to accept account changes.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if payload.text == current_user.email:
        log.info('set_user_email: same email address, no change necessary.')
        return { 'status': 'ok' }
    
    ret = await users.validate_email_address(payload.text)
    # when successful, validate_email_address() returns the Unicode normalized email in a msg field:
    if ret['success']:
        current_user.email = EmailStr(ret['msg'])
    else:
         # when unsuccessful, validate_email_address() returns an error description in a msg field:
         raise HTTPException( status_code=status.HTTP_406_NOT_ACCEPTABLE, 
                              detail=ret['msg'], 
                              headers={"WWW-Authenticate": "Bearer"}, 
                            )
    
    # generate a new email verification code:
    current_user.verify_code = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(16))
    
    # mark in user roles this user's email is unverified:
    current_user.roles = current_user.roles + ' unverified'
    
    # update user in the database: 
    id = await crud.put_user( current_user.id, current_user )
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await users.send_email_validation_email( current_user.username, current_user.email, current_user.verify_code )

    return { 'status': 'ok' }


# ----------------------------------------------------------------------------------------------
# Note: id's type is validated as greater than 0  
@router.delete("/users/disable", 
               status_code=status.HTTP_200_OK, 
               response_model=UserPublic, 
               summary="Disable the current user account.")
async def delete_user(current_user: UserInDB = Depends(users.get_current_active_user)):
    log.info( "delete_user: here!")
    # current_user is validated to be active, not disabled to get here, 
    # so its safe to directly disable:
    current_user.roles = current_user.roles + " disabled"
    id = await crud.put_user( current_user.id, current_user )
    if id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return  {"username": current_user.username, 
             "id": current_user.id, 
             "email": current_user.email, 
             "roles": current_user.roles}
