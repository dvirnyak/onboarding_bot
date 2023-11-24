from config import db_engine, db_meta, TELEGRAM_TOKEN

from telegram.ext import (Updater, CommandHandler,
                          CallbackQueryHandler, Filters,
                          MessageHandler)
import sqlalchemy as db
from base.models import Base
from commands.start import *
from commands.products import *


if __name__ == "__main__":
    # initialize database if it hasn't been yet
    db.MetaData.reflect(db_meta, bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    # run bot
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # distribute commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(products, pattern="products::"))
    dispatcher.add_handler(MessageHandler(Filters.text, products))

    # long poll
    updater.start_polling()
    updater.idle()
