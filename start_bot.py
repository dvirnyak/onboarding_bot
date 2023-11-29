from bot import start_bot
from config import db_engine, db_meta, TELEGRAM_TOKEN


from commands.main_menu import *
from data.insert_to_db import run_insertions

if __name__ == "__main__":
    # initialize database if it hasn't been yet
    db.MetaData.reflect(db_meta, bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    run_insertions()
    start_bot()
