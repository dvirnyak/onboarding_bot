from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from config import Session, BLOCKS_COUNT, ADMIN_KEY, stickers
from base.utils import *
from base.models import *

import pandas as pd
import matplotlib.pyplot as plt


async def admin_distribute_text(update: Update, context: CallbackContext,
                                user: User, session: Session):
    pass


async def notify(user: User, session: Session, type=""):
    pass


async def admin_help(update: Update, context: CallbackContext,
                     user: User, session: Session):
    pass


async def admin_login(update: Update, context: CallbackContext,
                      user: User, session: Session):
    if update.message.text == ADMIN_KEY:
        user.is_admin = True
        message_text = "🔓 Вы успешно вошли в панель администратора"
        await context.bot.send_sticker(chat_id=user.chat_id,
                                       sticker=stickers["turn"])
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")
        user.state = "admin_start"
        user.save(session)
    else:
        message_text = ("🔐 Не получается войти"
                        f"\n\nПроверьте данные и введите 🔑 ключ заново"
                        ""
                        "\n\nЕсли вы попали сюда случайно, то просто нажмите назад")
        keyboard = [[InlineKeyboardButton(
            "◀️ Назад", callback_data=f'menu::main_{user.button_number}')]]
        markup = InlineKeyboardMarkup(keyboard)
        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text=message_text,
                                                 reply_markup=markup,
                                                 parse_mode="HTML")
        user.last_message_id = message.message_id
        user.state = "admin_login"
        user.save(session)
