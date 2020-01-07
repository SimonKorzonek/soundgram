import os

class Config:
    SECRET_KEY = 'jh592nslk4829834ns9fj49jfe95'  # it should be in system variable
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # relative path from current file
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
