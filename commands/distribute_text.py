from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from base.utils import get_user
from config import Session, BLOCKS_COUNT
from commands.quizes import begin_quiz
from commands.products import next_product, previous_product
from commands.main_menu import main_menu


async def distribute_text(update: Update, context: CallbackContext):
    session = Session()
    user = await get_user(update, session)

    user.button_number += 1
    if user.state == "quiz_finished":
        if user.max_block < BLOCKS_COUNT:
            await begin_quiz(update, context, user, session)
        await main_menu(update, context, user, session)

    elif update.message.text == "Дальше" and user.state == "product_watching":
        await next_product(update, context, user, session)

    elif update.message.text == "Назад" and user.state == "product_watching":
        await previous_product(update, context, user, session)

    else:
        user.state = "start"
        await main_menu(update, context, user, session)
