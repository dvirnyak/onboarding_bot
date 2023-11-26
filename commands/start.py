from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from base.utils import get_user
from config import Session, BLOCKS_COUNT
from commands.main_menu import main_menu


async def start(update: Update, context):
    session = Session()
    user = await get_user(update, session)

    markup = None
    message_text = ""

    if user.state == "quiz_solving":
        message_text = "У вас начат тест. Сначала закончите его"

    elif user.state == "initial":
        user.state = "start"
        message_text = ("Привет, это обучающий бот 🤖"
                        f"\n\nВам будут показаны {BLOCKS_COUNT} блоков товаров и информация о них. Их нужно выучить"
                        ""
                        "\n\nВ конце каждого блока будет небольшой тест на время по изученному материалу"
                        ""
                        "\n\nПриступим?")
        keyboard = [
            [InlineKeyboardButton("Начать", callback_data=f'products::begin_{user.button_number}')],
            [InlineKeyboardButton("Ещё ⚙️", callback_data=f'menu::more_{user.button_number}')]
        ]
        markup = InlineKeyboardMarkup(keyboard)

    else:
        user.state = "start"
        await main_menu(update, context, user, session)
        return

    await context.bot.send_message(chat_id=user.chat_id,
                                   text=message_text,
                                   reply_markup=markup)

    user.save(session)
