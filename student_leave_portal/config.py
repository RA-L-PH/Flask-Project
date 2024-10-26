import os

class Config:
    SECRET_KEY = 'FlaskApIApP'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///leave.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
