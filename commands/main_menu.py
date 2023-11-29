import random
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from config import Session, BLOCKS_COUNT, smiles_gradient
from base.utils import *
from base.models import *
from commands.bot_utils import button_handler, choose_block_template
from commands.products import products_begin
from commands.quizes import begin_quiz

import pandas as pd
import matplotlib.pyplot as plt


@button_handler
async def menu_handler(update: Update, context: CallbackContext,
                       user: User, session: Session, action: str):
    if user.last_msg_is_photo:
        await context.bot.deleteMessage(chat_id=user.chat_id,
                                        message_id=user.last_message_id)
        user.last_msg_is_photo = False
        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text="Перенаправляю..")
        user.last_message_id = message.message_id
        user.state = "main_menu"

    action = action[len("menu::"):]
    action_fields = action.split("_")
    data = action_fields[-1]
    action_command = "_".join(action_fields[:-1])

    if data.isnumeric():
        data = int(data)
        await eval(f"{action_command}(update, context, user, session, data)")
    else:
        if action == "main":
            action = "main_menu"

        await eval(f"{action}(update, context, user, session)")

    user.save(session)


async def main_menu(update: Update, context: CallbackContext,
                    user: User, session: Session):
    if user.state == "quiz_solving":
        message_text = "У вас начат тест. Сначала закончите его"
        user.last_message_id = await context.bot.send_message(
            chat_id=user.chat_id, text=message_text)
        user.save(session)
        return

    message_text = f"<b>{random.choice('📕📗📘📙📚📒')} Меню</b>\n\n"
    if user.max_block == BLOCKS_COUNT:
        message_text += ("🏁 Вы завершили все блоки\n\n"
                         "Можете пройти обучение ещё раз или улучшить результаты тестов")
    else:
        message_text += (f"📌 Вы завершили {user.max_block} из {BLOCKS_COUNT} блоков \n\n"
                         f"Можете улучшить текущие результаты или пройти оставшийся материал")

    keyboard = []
    if user.current_block != BLOCKS_COUNT:
        keyboard.append([InlineKeyboardButton("⏯ Продолжить",
                                              callback_data=f'menu::continue_study_{user.button_number}')])
    keyboard += [[InlineKeyboardButton("📊 Результаты",
                                       callback_data=f'menu::watch_results_{user.button_number}')],
                 [InlineKeyboardButton("✍️ Пройти обучение",
                                       callback_data=f'menu::choose_study_block_{user.button_number}')],
                 [InlineKeyboardButton("🔄 Пройти тесты",
                                       callback_data=f'menu::choose_test_{user.button_number}')],
                 [InlineKeyboardButton("⚙️ Ещё",
                                       callback_data=f'menu::more_{user.button_number}')]]

    markup = InlineKeyboardMarkup(keyboard)

    if user.state == "main_menu":
        await context.bot.edit_message_text(chat_id=user.chat_id,
                                            message_id=user.last_message_id,
                                            text=message_text,
                                            reply_markup=markup,
                                            parse_mode="HTML")
    else:
        user.state = "main_menu"

        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text=message_text,
                                                 reply_markup=markup,
                                                 parse_mode="HTML")
        user.last_message_id = message.message_id

    user.save(session)


async def watch_results(update: Update, context: CallbackContext,
                        user: User, session: Session):
    message_text, image = await get_formatted_user_results(user, session)

    # form the keyboard
    keyboard = []
    if user.current_block != BLOCKS_COUNT:
        keyboard.append([InlineKeyboardButton("⏯ Продолжить",
                                              callback_data=f'menu::continue_study_{user.button_number}')])
    keyboard += [[InlineKeyboardButton(
        "✍️ Пройти обучение", callback_data=f'menu::choose_study_block_{user.button_number}')],
        [InlineKeyboardButton(
            "🔄 Пройти тесты", callback_data=f'menu::choose_test_{user.button_number}')],
        [InlineKeyboardButton(
            "◀️ Назад", callback_data=f'menu::main_{user.button_number}')]]
    markup = InlineKeyboardMarkup(keyboard)

    # delete previous, so we can add photo
    await context.bot.deleteMessage(chat_id=user.chat_id,
                                    message_id=user.last_message_id)
    message = await context.bot.send_photo(chat_id=user.chat_id, photo=image,
                                           caption=message_text, parse_mode='HTML',
                                           reply_markup=markup)
    user.last_msg_is_photo = True
    user.last_message_id = message.message_id
    user.state = "watching_results"
    user.save(session)


async def choose_test(update: Update, context: CallbackContext,
                      user: User, session: Session):
    start_message = f"<b>Выберите тест:</b>\n\n"
    button_text = "Тест"
    block_query = f'menu::test_block'
    back_query = f'menu::main_{user.button_number}'

    await choose_block_template(update, context,
                                user, session,
                                start_message, button_text,
                                block_query, back_query)


async def test_block(update: Update, context: CallbackContext,
                     user: User, session: Session, block: int):
    if user.max_block > block:
        user.current_block = block
        await begin_quiz(update, context, user, session)
    else:
        user.button_number -= 1

    user.save(session)


async def choose_study_block(update: Update, context: CallbackContext,
                             user: User, session: Session):
    start_message = f"<b>Выберите блок:</b>\n\n"
    button_text = "Блок"
    block_query = f'menu::study_block'
    back_query = f'menu::main_{user.button_number}'

    await choose_block_template(update, context,
                                user, session,
                                start_message, button_text,
                                block_query, back_query)


async def study_block(update: Update, context: CallbackContext,
                      user: User, session: Session, block: int):
    if user.max_block >= block:
        user.current_block = block
        user.current_product = 0
        await products_begin.__wrapped__(
            update, context, user, session)
    else:
        user.button_number -= 1

    user.save(session)


async def continue_study(update: Update, context: CallbackContext,
                         user: User, session: Session):
    await context.bot.deleteMessage(chat_id=user.chat_id,
                                    message_id=user.last_message_id)
    if user.current_block < BLOCKS_COUNT:
        await products_begin.__wrapped__(update, context, user, session)


async def more(update: Update, context: CallbackContext,
               user: User, session: Session):
    message_text = ("🔐 <b>Панель администратора </b>"
                    f"\n\nВведите 🔑 ключ администратора для входа"
                    ""
                    "\n\nЕсли вы попали сюда случайно, то просто нажмите назад")
    keyboard = [[InlineKeyboardButton(
        "◀️ Назад", callback_data=f'menu::main_{user.button_number}')]]
    markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.edit_message_text(chat_id=user.chat_id,
                                                  text=message_text,
                                                  message_id=user.last_message_id,
                                                  reply_markup=markup,
                                                  parse_mode="HTML")
    user.last_message_id = message.message_id
    user.state = "admin_login"
    user.save(session)
