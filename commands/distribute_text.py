from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from base.utils import get_user
from commands.admin import admin_login, admin_distribute_text
from config import Session, BLOCKS_COUNT
from commands.quizes import begin_quiz
from commands.products import next_product, previous_product, products_begin
from commands.main_menu import main_menu


async def distribute_text(update: Update, context: CallbackContext):
    session = Session()
    user = await get_user(update, session)

    user.button_number += 1
    if user.is_admin:
        await admin_distribute_text(update, context, user, session)

    if user.state == "admin_login":
        await admin_login(update, context, user, session)
    elif user.state == "quiz_finished" and user.max_block < BLOCKS_COUNT\
            and update.message.text == "Продолжить":
        await products_begin.__wrapped__(update, context, user, session)

    elif update.message.text == "Дальше" and user.state == "product_watching":
        await next_product(update, context, user, session)

    elif update.message.text == "Назад" and user.state == "product_watching":
        await previous_product(update, context, user, session)

    else:
        if user.state == "product_watching" or user.state == "quiz_finished":
            message = await context.bot.send_message(chat_id=user.chat_id,
                                                     text="Перенаправляю в меню..",
                                                     reply_markup=ReplyKeyboardRemove())

            await context.bot.deleteMessage(chat_id=user.chat_id, message_id=message.message_id)

        user.state = "start"
        await main_menu(update, context, user, session)

    user.save(session)
