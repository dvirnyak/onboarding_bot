from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CallbackContext
import json

from config import Session, bot, BLOCKS_COUNT

from base.utils import get_user, get_product
from base.models import *

import commands
from commands.bot_utils import error_handler, button_handler, get_image
from commands.quizes import begin_quiz


async def show_product(update: Update, context: CallbackContext,
                       user: User, session: Session):
    product = await get_product(user.current_block, user.current_product, session)
    if product is None:
        text = "Продуктов не найдено.."
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=text)
        await error_handler(update, context, user, session)
        return

    num_products = len(session.query(Product)
                       .filter_by(block=user.current_block)
                       .all())
    text = product.tg_str() + f"\n\n<b>{user.current_product + 1} / {num_products}</b>"
    keyboard = [
        [KeyboardButton("Назад"),
         KeyboardButton("Дальше")],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    user.last_msg_has_keyboard = True
    image = await get_image(product.image_path, user, context)

    await context.bot.send_photo(chat_id=user.chat_id, photo=image,
                                 caption=text, parse_mode='HTML',
                                 reply_markup=markup)


@button_handler
async def products_begin(update: Update, context: CallbackContext,
                         user: User, session: Session, action: str = None):
    if user.current_block >= BLOCKS_COUNT:
        message_text = ("Поздравляю! Вы усвоили весь материал и прошли все тесты. \n\n"
                        "При необходимости это можно сделать ещё раз через меню")
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=message_text)
        await commands.main_menu.main_menu(update, context, user, session)
        return

    user.state = "product_watching"
    message_text = f"Блок продуктов {user.current_block + 1} 📦"
    last_message = await context.bot.send_message(chat_id=user.chat_id,
                                                  text=message_text)
    user.last_message_id = last_message.id
    await show_product(update, context, user, session)
    user.save(session)


async def next_product(update: Update, context: CallbackContext,
                       user: User, session: Session):
    num_products = len(session.query(Product)
                       .filter_by(block=user.current_block)
                       .all())

    if user.current_product + 1 >= num_products:
        message_text = "Вы посмотрели все продукты в этом блоке и теперь можете пройти тест"
        # Remove the reply markup
        await context.bot.send_message(chat_id=user.chat_id, text=message_text,
                                       reply_markup=ReplyKeyboardRemove())
        user.last_msg_has_keyboard = False

        await begin_quiz(update, context, user, session)
        return

    user.current_product += 1
    await show_product(update, context, user, session)
    user.save(session)


async def previous_product(update: Update, context: CallbackContext,
                           user: User, session: Session):
    if user.current_product == 0:
        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text="Перенаправляю в меню..",
                                                 reply_markup=ReplyKeyboardRemove())
        user.last_msg_has_keyboard = False
        await context.bot.deleteMessage(chat_id=user.chat_id, message_id=message.message_id)

        await commands.main_menu.main_menu(update, context, user, session)
        return

    user.current_product -= 1
    await show_product(update, context, user, session)
    user.save(session)
