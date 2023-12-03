import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from base.utils import get_user
from config import Session, BLOCKS_COUNT, stickers
from commands.main_menu import main_menu
import commands


async def start(update: Update, context: CallbackContext):
    session = Session()
    user = await get_user(update, session)

    if user.is_admin:
        user.state = "help"
        await commands.admin.admin_menu.admin_menu(update, context, user, session)
        user.save(session)
        return

    elif user.state == "quiz_solving":
        message_text = "У вас начат тест. Сначала закончите его"
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=message_text)
    elif user.state == "initial":
        await commands.admin.admin.notify(context, user, session, "register")
        user.state = "start"

        smile = random.choice('📕📗📘📙📚📒')
        message_text = ("🤖 Привет, это обучающий бот <i>Letique Cosmetics</i>"
                        f"\n\n📦 Вам будут показаны {BLOCKS_COUNT} блоков товаров и информация о них"
                        ""
                        "\n\n❓ В конце каждого блока небольшой тест по изученному материалу"
                        f"\n\nВ {smile} Меню /menu вы всегда сможете посмотреть результаты "
                        f"и вернуться к предыдущим блокам"
                        "\n\nПриступим?")
        keyboard = [
            [InlineKeyboardButton("▶️ Начать", callback_data=f'products::begin_{user.button_number}')],
            [InlineKeyboardButton("⚙ Ещё", callback_data=f'menu::more_{user.button_number}')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text=message_text,
                                                 reply_markup=markup,
                                                 parse_mode="HTML")
        user.last_message_id = message.message_id

        await context.bot.send_sticker(chat_id=user.chat_id,
                                       sticker=stickers['hello'])

    else:
        user.state = "start"
        await main_menu(update, context, user, session)
        return

    user.save(session)


async def help_handler(update: Update, context: CallbackContext):
    session = Session()
    user = await get_user(update, session)

    if user.is_admin:
        user.state = "help"
        await commands.admin.admin_menu.admin_menu(update, context, user, session)
        user.save(session)
        return

    if user.state == "quiz_solving":
        message_text = "У вас начат тест. Сначала закончите его"
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=message_text)
        user.save(session)
        return

    smile = random.choice('📕📗📘📙📚📒')
    message_text = ("🤖 Привет, это обучающий бот <i>Letique Cosmetics</i>"
                    f"\n\n📦 Вам будут показаны {BLOCKS_COUNT} блоков товаров и информация о них"
                    ""
                    "\n\n❓ В конце каждого блока небольшой тест по изученному материалу"
                    ""
                    f"\n\nЧерез {smile} Меню /menu вы можете:\n"
                    "- Посмотреть результаты\n"
                    "- Пройти обучение\n"
                    "- Пройти тесты\n")
    keyboard = [
        [InlineKeyboardButton(f"{smile} Меню", callback_data=f'menu::main_{user.button_number}')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(chat_id=user.chat_id,
                                             text=message_text,
                                             reply_markup=markup,
                                             parse_mode="HTML")
    user.last_message_id = message.message_id
    user.state = "main_menu"
    user.save(session)
