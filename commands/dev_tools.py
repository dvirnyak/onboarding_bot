from config import db_engine, db_meta, TELEGRAM_TOKEN

from commands.main_menu import *
from data.insert_to_db import run_insertions


async def delete_db():
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    run_insertions()
