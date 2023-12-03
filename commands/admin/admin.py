from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from commands.admin.admin_menu import admin_menu
from config import ADMIN_KEY, stickers
from base.utils import *
from base.models import *


async def notify(context: CallbackContext, user: User,
                 session: Session, notification_type: str):
    admins = session.query(User).filter_by(is_admin=True).all()

    notification_dictionary = {
        "register": (0, f"Пользователь {user.tg_str()}")
    }

    notification = 0b001 if notification_type == "register" else 0b000
    notification = 0b010 if notification_type == "quiz_finished" else notification
    notification = 0b010 if notification_type == "all_quizes_finished" else notification

    image = None
    # forming message
    message_text = f"📩 Уведомление\n\n"
    if notification_type == "register":
        message_text += (f"🆕 Пользователь {user.tg_str()} "
                         f"зарегистрировался в боте")
    elif notification_type == "quiz_finished":
        result = await get_test_results(user, session, user.current_block)
        percent = result['correct_percent']
        correct_count = result['correct_count']
        count = result['count']

        message_text += (f"✔️ Пользователь {user.tg_str()}\n"
                         f"закончил <b>Тест {user.current_block + 1}</b> с результатом "
                         f"<b>{percent} %</b>"
                         f"\n{correct_count} / {count}\n"
                         f"Попытка {result['attempt']}")
    elif notification_type == "all_quizes_finished":
        message_text, image = await get_formatted_user_results(user, session, admin_asked=True)
        message_text = (f"🏁 Пользователь {user.tg_str()} закончил все тесты\n\n"
                        + message_text)

    for admin in admins:
        if admin.admin_notifications & notification:
            if notification_type == "all_quizes_finished":
                await context.bot.send_photo(chat_id=admin.chat_id,
                                             caption=message_text,
                                             photo=image,
                                             parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=admin.chat_id,
                                               text=message_text,
                                               parse_mode="HTML")


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
        await admin_menu(update, context, user, session)
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
