import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

PROJECT_PATH = os.path.dirname(__file__)
DB_PATH = PROJECT_PATH + "/" + os.getenv('DB_PATH')

db_engine = create_engine("sqlite:////" + DB_PATH)
db_meta = db.MetaData()
Session = sessionmaker(bind=db_engine)
