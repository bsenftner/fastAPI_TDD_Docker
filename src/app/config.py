import logging
from pydantic import BaseSettings
from pathlib import Path
from functools import lru_cache

import os

# set up the logger:
log = logging.getLogger("uvicorn")


# One of pydantic's most useful applications is settings management.
# If you create a model that inherits from BaseSettings, the model initialiser will 
# attempt to determine the values of any fields not passed as keyword arguments by 
# reading from the environment. (Default values will still be used if the matching 
# environment variable is not set.) 
#
# Dotenv (.env) support
# Basically place settings & secrets inside a .env file. Then create a class inheriting
# from BaseSettings with an inner class named 'Config' with a member field 'env_file'
# holding the path to the .env file. The .env file's contents will be loaded into the 
# same named class member fields. 
#
# Note: dotenv file parsing requires python-dotenv to be installed. This can be done 
# with either pip install python-dotenv or pip install pydantic[dotenv].

# old method directly used dotenv, but using new method we get type checking. 
# old method: 
'''
from dotenv import dotenv_values 
envConfig = dotenv_values(str(BASE_PATH / ".env"))  
#
print('envConfig is')
for key, value in envConfig.items():
    print(key, ' : ', value)
'''

# use pathlib to generate the "base path" of the application:
#
@lru_cache()
def get_base_path() -> Path:
    base_path = Path(__file__).resolve().parent
    return base_path

# print(f'config: BASE_PATH is {BASE_PATH}')


# see head of file comment, we're auto-loading Settings via a .env file
class Settings(BaseSettings):

    ENVIRONMENT: str                # dev, staging, prod
    TESTING: bool                   # in test mode or not
    
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    JWT_SECRET_KEY: str
    JWT_SECRET_REFRESH_KEY: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int
    REFRESH_TOKEN_EXPIRES_MINUTES: int
    JWT_ALGORITHM: str

    CLIENT_ORIGIN: str      # currently unused
    
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    # the presence of env_file within this child Config class 
    # tells Pydantic's BaseSettings to load our .env file
    class Config:
        env_file = str(get_base_path()) + '/.env'

@lru_cache()
def get_settings() -> BaseSettings:
    log.info("Loading config settings from the environment...")
    return Settings()

