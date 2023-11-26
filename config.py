import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

PROJECT_PATH = os.path.dirname(__file__)
DB_PATH = PROJECT_PATH + "/" + os.getenv('DB_PATH')
BLOCKS_COUNT = 6

db_engine = create_engine("sqlite:////" + DB_PATH)
db_meta = db.MetaData()
Session = sessionmaker(bind=db_engine, autoflush=False)

# Create the Application and pass it your bot's token.
bot = Application.builder().token(TELEGRAM_TOKEN).build()
stickers = {"respect": "CAACAgIAAxkBAAEXiu9lYr-WvQMQTq5dHQzB4XQXQK5lAQACPwAD29t-AAH05pw4AeSqaTME"}
