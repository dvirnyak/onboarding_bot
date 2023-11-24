from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from base.utils import get_user
from base.models import User
from config import Session


def start(update: Update, context):
    session = Session()
    user = get_user(update, session)
    user.state = "start"
    user.save(session)

    text = ("Привет, это обучающий бот 🤖"
            "\n\nТебе будут показаны 6 блоков товаров и информация о них. Их нужно выучить"
            ""
            "\n\nВ конце каждого блока будет небольшой тест на время по изученному материалу"
            ""
            "\n\nПриступим?")

    keyboard = [
        [InlineKeyboardButton("Начать", callback_data=f'products::begin_{user.button_number}')],
        [InlineKeyboardButton("Ещё ⚙️", callback_data=f'start::more_{user.button_number}')]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=user.chat_id,
                             text=text,
                             reply_markup=markup)


