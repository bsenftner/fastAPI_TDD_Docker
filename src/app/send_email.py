from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from jinja2 import Environment, select_autoescape, PackageLoader

from functools import lru_cache

from app.config import get_settings


# ----------------------------------------------------------------------------------------------
@lru_cache()
def get_jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader('app', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

# ----------------------------------------------------------------------------------------------
@lru_cache()
def get_emailConnectionConfig() -> ConnectionConfig:
    # 'settings' is application config settings
    settings = get_settings()
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS=True,
    )
    
# ----------------------------------------------------------------------------------------------
async def send_email_async(email_to: str, 
                           params: dict, 
                           templateName: str
                          ) -> JSONResponse:
    
    # print(json.dumps(params, indent = 4))
    
    # Generate the HTML template based on the template name
    # body is expected in this form:
    # { 'msg': { 'subject': 'the title', 'body':'this is the body'}}
    # template = env.get_template('basic_email.html')
    
    # here the passed template name is used to load the template:
    template = get_jinja_env().get_template(templateName)
    #
    # # the format of the msg dictionary is reliant on the template,
    # but in general they are something like:
    # { 'msg': { 'subject': 'the title', 'body':'this is the body'}}
    # i.e. a msg at the top with different named keys with values beneath
    #
    # here the values in msg are rendered into the template: 
    html = template.render( params )
    # print(html)
    
    # Define the message options
    message = MessageSchema(
            subject=params['msg']['subject'],
            recipients=[email_to],
            body=html,
            subtype="html"
    )
    
    conf = get_emailConnectionConfig()
    #
    # make the connection:
    fm = FastMail(conf)
    #
    # send the email:
    await fm.send_message(message)
    
    return JSONResponse(status_code=200, content={"message": "email has been sent"})
    

# ----------------------------------------------------------------------------------------------
def send_email_background( background_tasks: BackgroundTasks, 
                           subject: str, 
                           email_to: str, 
                           body: dict
                         ):
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    ) 
       
    conf = get_emailConnectionConfig()
    #
    # make the connection:
    fm = FastMail(conf)
    #
    # send the email:
    background_tasks.add_task( fm.send_message, message, template_name='basic_email.html' )
    
    return JSONResponse(status_code=200, content={"message": "email has been queued to be sent."})
