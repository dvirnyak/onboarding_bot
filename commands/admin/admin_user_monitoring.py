from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

import commands
from base.images import results_statistics_image, user_blocks_statistics
from config import Session, BLOCKS_COUNT, smiles_gradient, stickers
from base.utils import *
from base.models import *
from commands.bot_utils import form_paged_message

import pandas as pd
import matplotlib.pyplot as plt

page_size = 5
threshold = 75


async def users_monitoring(update: Update, context: CallbackContext,
                           admin: User, session: Session):
    message_text = (f"<b>👥 Пользователи</b>\n\n"
                    f"✅ Здесь вы можете посмотреть статистику и текущий прогресс по курсу, "
                    f"а также отправить уведомления")
    keyboard = []

    keyboard += [[InlineKeyboardButton(
        "📊 Результаты",
        callback_data=f'admin_menu::user_results_menu_0_{admin.button_number}')],
        [InlineKeyboardButton(
            "😴 Не закончившие",
            callback_data=f'admin_menu::sleeping_0_{admin.button_number}')],
        [InlineKeyboardButton(
            f"📉 С низкими результатами ( < {threshold} % )",
            callback_data=f'admin_menu::low_results_0_{admin.button_number}')],
        [InlineKeyboardButton(
            "◀️ Выход",
            callback_data=f'admin_menu::menu_{admin.button_number}')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    image = await user_blocks_statistics(session)

    await context.bot.deleteMessage(chat_id=admin.chat_id,
                                    message_id=admin.last_message_id)
    message = await context.bot.send_photo(chat_id=admin.chat_id,
                                           photo=image,
                                           caption=message_text,
                                           reply_markup=markup,
                                           parse_mode="HTML")
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = True
    admin.admin_current_page = 0

    admin.save(session)


async def user_results_menu(update: Update, context: CallbackContext,
                            admin: User, session: Session, data: int):
    async def button_maker(users, i):
        button_text = f"{users[i].name_str()}"
        query = f"admin_menu::user_results_{users[i].chat_id}_{admin.button_number}"
        return button_text, query

    users = session.query(User).all()
    backward_query = f'admin_menu::user_results_menu_1_{admin.button_number}'
    forward_query = f'admin_menu::user_results_menu_2_{admin.button_number}'

    start_message = ("<b>📊  Результаты пользователей</b>\n\n"
                     "📃 Чтобы посмотреть подробнее, нажмите на "
                     "соответсвующую кнопку\n\n")
    key = None
    image = await results_statistics_image(session)

    await template(update, context, admin, session, data,
                   button_maker,
                   start_message, key, image,
                   backward_query, forward_query, users)


async def user_results(update: Update, context: CallbackContext,
                       admin: User, session: Session, data: int):
    user = session.query(User).filter_by(chat_id=data).first()
    if user is None:
        return

    image = await get_tests_results(user, session)
    message_text, image = await get_formatted_user_results(user, session, admin_asked=True)
    keyboard = [[InlineKeyboardButton(
        text=f"◀️ Назад", callback_data=f'admin_menu::user_results_menu_0_{admin.button_number}')]]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.deleteMessage(chat_id=admin.chat_id,
                                    message_id=admin.last_message_id)
    message = await context.bot.send_photo(
        chat_id=admin.chat_id,
        caption=message_text,
        parse_mode="HTML",
        reply_markup=markup,
        photo=image
    )
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = True
    admin.save(session)


async def sleeping(update: Update, context: CallbackContext,
                   admin: User, session: Session, data: int):
    async def button_maker(users, i):
        return None, None

    users = session.query(User).filter(User.max_block < 6).all()
    backward_query = f'admin_menu::sleeping_1_{admin.button_number}'
    forward_query = f'admin_menu::sleeping_2_{admin.button_number}'

    start_message = ("<b>😴 Не закончившие тесты</b>\n\n"
                     "🔊 Вы можете отправить им уведомление"
                     "\n\n")

    key = [[InlineKeyboardButton(
        text=f"🔊 Отправить уведомление",
        callback_data=f"admin_menu::sleeping_notify_{admin.button_number}")]]

    image = await user_blocks_statistics(session)

    await template(update, context, admin, session, data,
                   button_maker,
                   start_message, key, image,
                   backward_query, forward_query, users)


async def low_results(update: Update, context: CallbackContext,
                      admin: User, session: Session, data: int):
    async def button_maker(users, i):
        return None, None

    all_users = session.query(User).filter().all()
    users = []
    for user in all_users:
        results, average = await get_tests_results(user, session)
        if average < threshold:
            users.append(user)

    backward_query = f'admin_menu::low_results_1_{admin.button_number}'
    forward_query = f'admin_menu::low_results_2_{admin.button_number}'

    start_message = (f"📉<b> С низкими результатами ( &lt; {threshold} % ) </b>\n\n"
                     "🔊 Вы можете отправить им уведомление"
                     "\n\n")

    key = [[InlineKeyboardButton(
        text=f"🔊 Отправить уведомление",
        callback_data=f"admin_menu::low_results_notify_{admin.button_number}")]]

    image = await results_statistics_image(session)

    await template(update, context, admin, session, data,
                   button_maker,
                   start_message, key, image,
                   backward_query, forward_query, users)


async def template(update: Update, context: CallbackContext,
                   admin: User, session: Session, data: int,
                   button_maker,
                   start_message="", key=None, image=None,
                   backward_query="", forward_query="",
                   users=None):
    if data == 1:
        admin.admin_current_page -= 1
    elif data == 2:
        admin.admin_current_page += 1

    async def message_maker(users, i):
        user = users[i]
        results, average = await get_tests_results(user, session)
        user_text = (f"<b>{user.tg_str()} {len(results)} / {BLOCKS_COUNT}</b>\n"
                     f"📌 Среднее: <b>{average} %</b>\n\n")

        return user_text

    message_text, keyboard = await form_paged_message(users, message_maker,
                                                      button_maker, page_size,
                                                      admin.admin_current_page,
                                                      backward_query, forward_query)

    message_text = start_message + message_text
    if key is not None:
        keyboard += key

    keyboard += [[InlineKeyboardButton(
        text=f"◀️ Назад", callback_data=f"admin_menu::users_monitoring_{admin.button_number}")]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.deleteMessage(chat_id=admin.chat_id,
                                    message_id=admin.last_message_id)
    message = await context.bot.send_photo(chat_id=admin.chat_id,
                                           caption=message_text,
                                           parse_mode="HTML",
                                           reply_markup=markup,
                                           photo=image)
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = True
    admin.save(session)


async def sleeping_notify(update: Update, context: CallbackContext,
                          admin: User, session: Session, data: int = None):
    to_notify = False
    admin_letter = None
    if data is not None and data == 0:
        to_notify = True
    elif update.message is not None and update.message.text is not None:
        to_notify = True
        admin_letter = update.message.text
    else:
        message_text = ("🔊 Уведомление пользователям, не прошедшим тесты\n\n"
                        "✉️ Можете ввести своё сообщение:")
        admin.state = "sleeping_notify_confirm"
        keyboard = [[InlineKeyboardButton(
            text=f"Отправить без сообщения", callback_data=f'admin_menu::sleeping_notify_0_{admin.button_number}')],
            [InlineKeyboardButton(
                text=f"◀️ Назад", callback_data=f'admin_menu::sleeping_0_{admin.button_number}')]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML",
                                       reply_markup=markup)
    if to_notify:
        message_to_users = ("<b>📩 Уведомление от администратора</b>\n\n"
                            "<i>Вы получили это сообщение, потому что "
                            "прошли тестирование не до конца</i>\n\n")
        if admin_letter is not None:
            message_to_users += f"🗣 Сообщение администратора:\n{admin_letter}"

        users = session.query(User).filter(User.max_block < 6).all()
        for user in users:
            await context.bot.send_message(chat_id=user.chat_id,
                                           text=message_to_users,
                                           parse_mode="HTML")

        message_text = "✅ Разослано"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")
        await sleeping(update, context, admin, session, 0)
        admin.state = "admin_menu"

    admin.save(session)


async def low_results_notify(update: Update, context: CallbackContext,
                             admin: User, session: Session, data: int = None):
    to_notify = False
    admin_letter = None
    if data is not None and data == 0:
        to_notify = True
    elif update.message is not None and update.message.text is not None:
        to_notify = True
        admin_letter = update.message.text
    else:
        message_text = ("🔊 Уведомление пользователям с низкими результатами\n\n"
                        "✉️ Можете ввести своё сообщение:")
        admin.state = "low_results_confirm"
        keyboard = [[InlineKeyboardButton(
            text=f"Отправить без сообщения",
            callback_data=f'admin_menu::low_results_notify_0_{admin.button_number}')],
            [InlineKeyboardButton(
                text=f"◀️ Назад", callback_data=f'admin_menu::low_results_0_{admin.button_number}')]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML",
                                       reply_markup=markup)
    if to_notify:
        message_to_users = ("<b>📩 Уведомление от администратора</b>\n\n"
                            "<i>Вы получили это сообщение, потому что "
                            f"прошли тестирование с результатом &lt; {threshold} %</i>\n\n")
        if admin_letter is not None:
            message_to_users += f"🗣 Сообщение администратора:\n{admin_letter}"

        all_users = session.query(User).filter().all()
        users = []
        for user in all_users:
            results, average = await get_tests_results(user, session)
            if average < threshold:
                users.append(user)

        for user in users:
            await context.bot.send_message(chat_id=user.chat_id,
                                           text=message_to_users,
                                           parse_mode="HTML")

        message_text = "✅ Разослано"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")
        await sleeping(update, context, admin, session, 0)
        admin.state = "admin_menu"

    admin.save(session)
