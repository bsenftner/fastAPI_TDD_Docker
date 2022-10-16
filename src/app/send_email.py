import os
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from jinja2 import Environment, select_autoescape, PackageLoader
from app.config import settings 

from pathlib import Path
BASE_PATH = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------------------------
env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

# ----------------------------------------------------------------------------------------------
class EmailSchema(BaseModel):
   email: List[EmailStr]
   

# ----------------------------------------------------------------------------------------------
conf = ConnectionConfig(
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
'''
template = """
        <html>
            <body>
                <p>Hi !!!
                <br>Thanks for using fastapi mail, keep using it..!!!</p>
            </body>
        </html>
        """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=template,
        subtype='html',
    )
'''

# ----------------------------------------------------------------------------------------------
async def send_email_async(subject: str, email_to: str, body: dict):
    
    # Generate the HTML template based on the template name
    # body is expected in this form:
    # { 'body': { 'title': 'the title', 'name':'this is the body'}}
    template = env.get_template('email.html')
    #
    html = template.render( body )
    # print("send_email_async: rendered template:")
    # print(html)
    
    # Define the message options
    message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            body=html,
            subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})
    

# ----------------------------------------------------------------------------------------------
def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    )    
    
    fm = FastMail(conf)
    background_tasks.add_task( fm.send_message, message, template_name='email.html' )
    return JSONResponse(status_code=200, content={"message": "email has been queued to be sent."})