import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_KEY = os.getenv('ADMIN_KEY')

PROJECT_PATH = os.path.dirname(__file__)
DB_PATH = PROJECT_PATH + "/" + os.getenv('DB_PATH')
IMAGES_PATH = PROJECT_PATH + "/" + "data/images/"
BLOCKS_COUNT = 6

db_engine = create_engine("sqlite:////" + DB_PATH)
db_meta = db.MetaData()
Session = sessionmaker(bind=db_engine, autoflush=False)

# Create the Application and pass it your bot's token.
bot = Application.builder().token(TELEGRAM_TOKEN).build()
stickers = {"respect": "CAACAgIAAxkBAAEXiu9lYr-WvQMQTq5dHQzB4XQXQK5lAQACPwAD29t-AAH05pw4AeSqaTME",
            "congratulate": "CAACAgIAAxkBAAEXi-BlY1abcVxK0wlj-xDGBcJB-KybwgACZgAD29t-AAGTzMPQDS2PbDME",
            "hello": "CAACAgIAAxkBAAEXi-JlY1bGEuSHUiUbZzy_c1T4MwLTigACbwAD29t-AAGZW1Coe5OAdDME",
            "sleep": "CAACAgIAAxkBAAEXi-RlY1bcJhAhlKvYO65jwxVsPKZkJwACOAAD29t-AAHZk3yYN2zlLDME",
            "turn": "CAACAgIAAxkBAAEXi-ZlY1b5uxQAAQFgyx6kQ3v2wmVX2gIAAmoAA9vbfgAB8Y-y3zViFt8zBA",
            "sad": "CAACAgIAAxkBAAEXi-hlY1dEA7-LpSXlmoh9dzqKIPM03wACYgAD29t-AAGOFzVmmxPyHDME",
            "error": "CAACAgIAAxkBAAEXi-plY1dcApcqkudTqDRhRiMKLEsvfwACYwAD29t-AAGMnQU950KD5zME",
            "chill": "CAACAgIAAxkBAAEXi-xlY1d2ypEFJKGdXLBCjC4QPNwrmgACYAAD29t-AAGGKUzOUOHn4TME",
            "dance": "CAACAgIAAxkBAAEXi-5lY1eYARjQrKlwskLGNmtyVkLEgAACZwAD29t-AAE93xTvYUeRnzME",
            "think": "CAACAgIAAxkBAAEXi_JlY1fnIxl9ibrpm0kIseYzzdUl8gACXwAD29t-AAGEsFSbEa7K4zME"
            }
smiles_gradient = "☠️😵🫣☹️😐🥴🫠🤔🫡👍😤💪😎🥈🏆🥳"
images_cache = {}
