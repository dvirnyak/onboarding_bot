from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery, InputFile
from telegram.constants import ChatAction
from telegram.ext import CallbackContext

from base.utils import get_user
from base.models import *
from config import Session, IMAGES_PATH, images_cache, stickers, BLOCKS_COUNT
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


async def get_image(image_path: str, user: User, context: CallbackContext) -> str:
    image_path = IMAGES_PATH + image_path
    if not (image_path in images_cache):
        # if not, send the photo as a byte string and store its file_id
        await context.bot.send_chat_action(chat_id=user.chat_id, action=ChatAction.UPLOAD_PHOTO)
        with open(image_path, 'rb') as image:
            message = await context.bot.send_photo(chat_id=user.chat_id, photo=image)
            file_id = message.photo[-1].file_id
            images_cache[image_path] = file_id
            await context.bot.deleteMessage(chat_id=user.chat_id,
                                            message_id=message.message_id)

    return images_cache[image_path]


async def error_handler(update: Update, context: CallbackContext, user: User, session: Session):
    if not (context is None):
        await context.bot.send_sticker(chat_id=user.chat_id,
                                       sticker=stickers['error'])
        text = f"Что-то пошло не так. Возвращаю в главное меню"
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=text)

    await commands.main_menu.main_menu(update, context,
                                       user, session)
    user.save(session)


async def form_paged_message(objects: list, message_maker, button_maker,
                             page_size, current_page, back_query, forward_query):
    while len(objects) < page_size * current_page:
        current_page -= 1

    message_text = ""
    keyboard = []
    for i in range(page_size * current_page, min(len(objects),
                                                 page_size * (current_page + 1))):
        message_text += await message_maker(objects, i)
        button_text, query = await button_maker(objects, i)
        if button_text is not None:
            keyboard += [[InlineKeyboardButton(text=button_text, callback_data=query)]]

    last_row = []
    if current_page != 0:
        last_row += [InlineKeyboardButton(text="⬅️️", callback_data=back_query)]
    if (current_page + 1) * page_size < len(objects):
        last_row += [InlineKeyboardButton(text="➡️", callback_data=forward_query)]
    if len(last_row) > 0:
        keyboard += [last_row]

    return message_text, keyboard


async def choose_block_template(update: Update, context: CallbackContext,
                                user: User, session: Session,
                                start_message: str, button_text_base: str,
                                block_query: str, back_query: str):
    message_text = start_message
    keyboard = []
    for i in range(BLOCKS_COUNT):
        button_text = button_text_base + f" {i + 1}"
        if user.max_block < i and (not user.is_admin):
            button_text = "🔒 " + button_text
        elif user.max_block == i and (not user.is_admin) and button_text_base == "Тест":
            button_text = "🔒 " + button_text

        keyboard.append([InlineKeyboardButton(
            button_text, callback_data=block_query + f'_{i}_{user.button_number}')], )

    keyboard.append([InlineKeyboardButton(
        "◀️ Назад", callback_data=back_query)])

    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        message_id=user.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    if not user.is_admin:
        user.state = "main_menu"

    user.save(session)
