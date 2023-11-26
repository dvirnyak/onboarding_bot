from config import db_engine, db_meta, TELEGRAM_TOKEN

from telegram.ext import (Application, CommandHandler,
                          CallbackQueryHandler,
                          MessageHandler, filters)
import sqlalchemy as db
from base.models import Base
from commands.start import *
from commands.products import *
from commands.quizes import *
from commands.distribute_text import *
from commands.main_menu import *
from config import bot


def main():
    # initialize database if it hasn't been yet
    db.MetaData.reflect(db_meta, bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    # on different commands - answer in Telegram
    bot.add_handler(CommandHandler(["start", "menu"], start))
    bot.add_handler(CommandHandler(["help"], help_handler))
    bot.add_handler(CallbackQueryHandler(products_begin, pattern="products::begin"))
    bot.add_handler(CallbackQueryHandler(quiz_solving, pattern="quiz::"))
    bot.add_handler(CallbackQueryHandler(menu_handler, pattern="menu::"))
    bot.add_handler(
        MessageHandler(callback=distribute_text, filters=filters.BaseFilter(filters.TEXT))
    )

    # Run the bot until the user presses Ctrl-C
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
