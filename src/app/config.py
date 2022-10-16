# see: https://codevoweb.com/restful-api-with-python-fastapi-access-and-refresh-tokens/
# describes this file's setup, and usage 

from pydantic import BaseSettings

from pathlib import Path
#
ENV_PATH = Path(__file__).resolve().parent
# print(f'config: env_path is {ENV_PATH}')

class Settings(BaseSettings):

    JWT_SECRET_KEY: str
    JWT_SECRET_REFRESH_KEY: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int
    REFRESH_TOKEN_EXPIRES_MINUTES: int
    JWT_ALGORITHM: str

    CLIENT_ORIGIN: str      # currently unused
    
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    class Config:
        env_file = str(ENV_PATH) + '/.env'


settings = Settings()

