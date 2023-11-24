from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from config import Session
from base.utils import get_user
from base.models import *
from config import Session


def quiz_solving(update: Update, context: CallbackContext):
    session = Session()
    user = get_user(update, session)
    action = ''

    query = update.callback_query
    if query is None:
        if update.message.text == "Дальше" and user.state == "product_watching":
            action = "products::next"
    elif not (query is None):
        query.answer()

        action, button_number = query.data.split("_")
        print(action, button_number)

        if not button_number.isnumeric() or int(button_number) < user.button_number:
            return session.commit()

        user.button_number += 1