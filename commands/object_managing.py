import uuid
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery, InputFile
from telegram.constants import ChatAction
from telegram.ext import CallbackContext

from base.clear_text import clear_text_arr
from base.utils import get_user
from base.models import *
from config import Session, IMAGES_PATH, images_cache, stickers, BLOCKS_COUNT
from functools import wraps
import commands


async def admin_add_object(update: Update, context: CallbackContext,
                           admin: User, session: Session, fields: dict):
    cache = {}
    if admin.admin_cache is None or admin.admin_cache == "null":
        cache['current_field'] = -1
        cache['values'] = {}
        admin.admin_cache = json.dumps(cache)

    cache = json.loads(admin.admin_cache)
    current_field = cache['current_field']
    field = fields['stages'][current_field]

    # save the result of the previous step
    is_input_correct = False
    if current_field >= 0:
        if (field['type'] == 'text'
                and update is not None
                and update.message is not None
                and update.message.text is not None):
            cache['values'][str(current_field)] = update.message.text
            is_input_correct = True

        elif (field['type'] == "image"
              and update is not None
              and update.message is not None
              and hasattr(update.message, 'photo')
              and len(update.message.photo) > 0):

            photo_file_id = update.message.photo[-1].file_id
            photo_file = await context.bot.get_file(photo_file_id)
            # Generate a unique filename for the photo
            filename = str(uuid.uuid4()) + '.jpg'

            # Download the photo to the server
            with open(IMAGES_PATH + filename, 'wb') as file:
                await photo_file.download_to_memory(file)

            images_cache[filename] = photo_file_id
            cache['values'][str(current_field)] = filename
            is_input_correct = True

        elif (field['type'] == 'list'
              and update is not None
              and update.message is not None
              and update.message.text is not None):

            arr = update.message.text.split("\n")
            arr = clear_text_arr(arr)

            cache['values'][str(current_field)] = json.dumps(arr)
            is_input_correct = True

    if is_input_correct:
        message_text = "✅ Данные сохранены"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text)
    elif current_field > 0:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])

        message_text = "❌ Некорректный ввод\n\n<i>Попробуйте снова</i>"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")
        current_field -= 1

    current_field += 1
    cache['current_field'] = current_field

    finished = False
    if current_field == len(fields['stages']):
        finished = True
        # the input is over
        message_text = f"✅ Вы успешно добавили {fields['title']} <b>{cache['values']['0']}</b>!"

        if fields['object_type'] == "product":
            await context.bot.send_message(chat_id=admin.chat_id,
                                           text=message_text,
                                           parse_mode="HTML")
            product = Product(title=cache['values']['0'],
                              description=cache['values']['1'],
                              price=cache['values']['2'],
                              together=cache['values']['3'],
                              effects=cache['values']['4'],
                              image_path=cache['values']['5'],
                              block=admin.current_block)

            session.add(product)
        elif fields['object_type'] == 'question':
            question = Question(text=cache['values']['0'],
                                options=cache['values']['1'],
                                correct_answer=cache['values']['2'],
                                block=admin.current_block)
            session.add(question)

        cache = None
        admin.state = "admin_menu"

    else:
        field = fields['stages'][current_field]
        message_text = field['enter_text']
        admin.state = fields['state']

    keyboard = []
    keyboard += [[InlineKeyboardButton(
        text=f"❌ Отмена",
        callback_data=fields['cancel_button_query'] + f"_{admin.button_number}")]]

    markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(chat_id=admin.chat_id,
                                             text=message_text,
                                             parse_mode="HTML",
                                             reply_markup=markup)
    admin.last_message_id = message.message_id
    admin.admin_cache = json.dumps(cache)

    admin.save(session)

    if finished:
        await fields['coroutine_after_finished']


async def admin_edit_object(update: Update, context: CallbackContext,
                            admin: User, session: Session, fields: dict,
                            object, is_answered: bool):
    field = fields['property']

    # save the result of the previous step
    is_input_correct = False
    if is_answered:
        if (field['type'] == 'text'
                and update is not None
                and update.message is not None
                and update.message.text is not None):

            setattr(object, field['attr'], update.message.text)
            is_input_correct = True

        elif (field['type'] == "image"
              and update is not None
              and update.message is not None
              and hasattr(update.message, 'photo')
              and len(update.message.photo) > 0):

            photo_file_id = update.message.photo[-1].file_id
            photo_file = await context.bot.get_file(photo_file_id)
            # Generate a unique filename for the photo
            filename = str(uuid.uuid4()) + '.jpg'

            # Download the photo to the server
            with open(IMAGES_PATH + filename, 'wb') as file:
                await photo_file.download_to_memory(file)

            images_cache[filename] = photo_file_id
            setattr(object, field['attr'], filename)
            is_input_correct = True

        elif (field['type'] == 'list'
              and update is not None
              and update.message is not None
              and update.message.text is not None):

            arr = update.message.text.split("\n")
            arr = clear_text_arr(arr)

            setattr(object, field['attr'], json.dumps(arr))
            is_input_correct = True

    if is_input_correct:
        # the input is over
        message_text = f"✅ Вы успешно обновили {fields['title']}!"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")

        admin.state = "admin_menu"

    elif is_answered and not is_input_correct:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])

        message_text = "❌ Некорректный ввод\n\n<i>Попробуйте снова</i>"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text,
                                       parse_mode="HTML")

    else:
        field = fields['property']
        message_text = field['enter_text']
        admin.state = fields['state']

    keyboard = []
    keyboard += [[InlineKeyboardButton(
        text=f"❌ Отмена",
        callback_data=fields['cancel_button_query'] + f"_{admin.button_number}")]]

    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        text=message_text,
                                        parse_mode="HTML",
                                        reply_markup=markup,
                                        message_id=admin.last_message_id)
    admin.save(session)

    if is_input_correct and is_answered:
        await fields['coroutine_after_finished']
