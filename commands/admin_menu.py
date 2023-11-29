import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

import commands
from config import Session, BLOCKS_COUNT, smiles_gradient, stickers
from base.models import *
from commands.bot_utils import button_handler, form_paged_message, choose_block_template

page_size = 5


async def admin_menu(update: Update, context: CallbackContext,
                     admin: User, session: Session):
    message_text = (f"<b>{random.choice('💻🖥🕹🎛📻🗄🗂')} Панель администратора Letique Cosmetics</b>\n\n"
                    f"📋 Здесь вы можете: \n"
                    f"- Посмотреть статистику\n"
                    f"- Добавить или удалить вопросы и тесты\n"
                    f"- Настроить уведомления\n"
                    f"- Отправить напоминания пользователям\n\n"
                    f"✅ Ищите функции в соответствующих разделах")
    keyboard = []

    keyboard += [[InlineKeyboardButton(
        "📩 Настройки уведомлений",
        callback_data=f'admin_menu::notification_settings_999_{admin.button_number}')],
        [InlineKeyboardButton(
            "👤  Пользователи",
            callback_data=f'admin_menu::users_monitoring_{admin.button_number}')],
        [InlineKeyboardButton(
            "📋 Тесты",
            callback_data=f'admin_menu::questions_settings_{admin.button_number}')],
        [InlineKeyboardButton(
            "📦 Продукты",
            callback_data=f'admin_menu::products_settings_{admin.button_number}')],
        [InlineKeyboardButton(
            "❌ Выход",
            callback_data=f'admin_menu::exit_admin_{admin.button_number}')],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if admin.state == "admin_menu":
        await context.bot.edit_message_text(chat_id=admin.chat_id,
                                            message_id=admin.last_message_id,
                                            text=message_text,
                                            reply_markup=markup,
                                            parse_mode="HTML")
    else:
        admin.state = "admin_menu"

        message = await context.bot.send_message(chat_id=admin.chat_id,
                                                 text=message_text,
                                                 reply_markup=markup,
                                                 parse_mode="HTML")
        admin.last_message_id = message.message_id

    admin.save(session)


async def notification_settings(update, context, admin, session, data):
    # change the notifications
    if data != 999:
        if admin.admin_notifications & (2 ** data):
            admin.admin_notifications -= 2 ** data
        else:
            admin.admin_notifications += 2 ** data

    smiles = {True: "🟢", False: "🔴"}
    # display them
    message_text = ("📩 Уведомления\n\n"
                    "✅ Чтобы подписаться/отписаться, нажмите на нужную категорию")

    keyboard = [[InlineKeyboardButton(
        f"{smiles[bool(admin.admin_notifications & (2 ** 0))]} Новый пользователь 👤",
        callback_data=f'admin_menu::notification_settings_0_{admin.button_number}')],
        [InlineKeyboardButton(
            f"{smiles[bool(admin.admin_notifications & (2 ** 1))]} Тест пройден ✔️",
            callback_data=f'admin_menu::notification_settings_1_{admin.button_number}')],
        [InlineKeyboardButton(
            f"{smiles[bool(admin.admin_notifications & (2 ** 2))]} Все тесты пройдены 🏁",
            callback_data=f'admin_menu::notification_settings_2_{admin.button_number}')],
        [InlineKeyboardButton(
            "◀️ Выход",
            callback_data=f'admin_menu::menu_{admin.button_number}')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        message_id=admin.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    admin.save(session)


async def exit_admin(update, context, admin, session):
    admin.is_admin = False
    admin.current_block = 0
    message_text = "🔐 Вы успешно вышли из панели администратора"
    await context.bot.send_sticker(chat_id=admin.chat_id,
                                   sticker=stickers["turn"])
    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        text=message_text,
                                        message_id=admin.last_message_id,
                                        parse_mode="HTML")
    admin.state = "start"
    await commands.main_menu.main_menu(update, context, admin, session)
    admin.save(session)
