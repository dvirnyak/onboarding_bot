from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update,
                      KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import CallbackContext
from config import Session
from base.utils import get_user, get_product
from base.models import *
from config import Session
import json


def get_product_text(product: Product):
    text = (f"*{product.title}*\n\n"
            f"Описание: {product.description}\n\n"
            f"Цена: {product.price}\n\n"
            f"Используют вместе с ")
    text += ", ".join(json.loads(product.together))
    text += "\n\nЭффекты: " + ", ".join(json.loads(product.together))

    return text


def products(update: Update, context: CallbackContext):
    session = Session()
    user = get_user(update, session)
    action = ''

    query = update.callback_query
    if query is None:
        # TODO назад
        if update.message.text == "Дальше" and user.state == "product_watching":
            action = "products::next"
    elif not (query is None):
        query.answer()

        action, button_number = query.data.split("_")
        print(action, button_number)

        if not button_number.isnumeric() or int(button_number) < user.button_number:
            return session.commit()

        user.button_number += 1

    if action == "products::begin":
        user.state = "product_watching"
        user.current_product = 0

        text = f"Блок продуктов {user.current_block + 1} 📦"
        context.bot.send_message(chat_id=user.chat_id,
                                 text=text)
        action = "products::next"

    if action == "products::next":
        product = get_product(user.current_block, user.current_product, session)
        if product is None:
            return session.commit()

        user.current_product += 1
        if user.current_product \
                >= len(session.query(Product).filter_by(block=user.current_block).all()):
            user.state = "begin_test"

        text = get_product_text(product)

        keyboard = [
            [KeyboardButton("Дальше")],
            [KeyboardButton("Назад")]
        ]

        markup = ReplyKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=user.chat_id,
                                 text=text, parse_mode='MarkdownV2',
                                 reply_markup=markup)

    user.save(session)
