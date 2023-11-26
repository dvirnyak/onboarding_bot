from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from base.utils import get_user
from base.models import *
from config import Session
from functools import wraps
import commands


def button_handler(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        query = update.callback_query
        if query is None:
            return
        await query.answer()

        session = Session()
        user = await get_user(update=update, session=session)

        data = query.data.split("_")
        action = "_".join(data[:-1])
        button_number = data[-1]
        if not button_number.isnumeric() or int(button_number) < user.button_number:
            return None
        user.button_number += 1

        return await func(update, context, user, session, action)

    return wrapper


async def error_handler(update: Update, context: CallbackContext, user: User, session: Session):
    if not (context is None):
        text = f"Что-то пошло не так. Возвращаю в главное меню"
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=text)


    await commands.main_menu.main_menu(update, context,
                                       user, session)
    user.save(session)
