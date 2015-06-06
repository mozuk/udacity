from flask import Flask
from database_setup import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask import session as login_session
from flask.ext.heroku import Heroku

APPLICATION_NAME = "Catalog Application"
app = Flask(__name__)

heroku = Heroku(app)

# Connect to Database and create database session
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()
