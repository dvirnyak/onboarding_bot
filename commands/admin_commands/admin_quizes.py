from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from commands.object_managing import admin_add_object, admin_edit_object
from config import Session, stickers
from base.utils import *
from base.models import *
from commands.bot_utils import form_paged_message, choose_block_template, get_image, error_handler

page_size = 5


async def questions_settings(update: Update, context: CallbackContext,
                             admin: User, session: Session):
    start_message = f"<b>Выберите тест:</b>\n\n"
    button_text = "Тест"
    block_query = f'admin_menu::questions_block_chosen'
    back_query = f'admin_menu::menu_{admin.button_number}'

    await choose_block_template(update, context,
                                admin, session,
                                start_message, button_text,
                                block_query, back_query)


async def questions_block(update: Update, context: CallbackContext,
                          admin: User, session: Session, data: int):
    admin.admin_cache = json.dumps(None)
    if data == 1:
        admin.admin_current_page -= 1
    elif data == 2:
        admin.admin_current_page += 1

    async def message_maker(questions, i):
        question = questions[i]
        question_text = f"- <b>{question}</b>\n\n"
        question_text = ""

        return question_text

    async def button_maker(questions, i):
        button_text = f"{questions[i]}"
        query = f"admin_menu::watch_question_{i}_{admin.button_number}"
        return button_text, query

    questions = session.query(Question).filter_by(block=admin.current_block).all()

    backward_query = f'admin_menu::questions_block_1_{admin.button_number}'
    forward_query = f'admin_menu::questions_block_2_{admin.button_number}'

    start_message = (f"<b>📝 Тест {admin.current_block + 1}</b>\n\n"
                     "📃 Чтобы посмотреть подробнее, нажмите на "
                     "соответсвующую кнопку\n\n")

    message_text, keyboard = await form_paged_message(questions, message_maker,
                                                      button_maker, page_size,
                                                      admin.admin_current_page,
                                                      backward_query, forward_query)

    message_text = start_message + message_text

    keyboard += [[InlineKeyboardButton(
        text=f"🆕 Добавить", callback_data=f"admin_menu::questions_add_{admin.button_number}")]]

    keyboard += [[InlineKeyboardButton(
        text=f"◀️ Назад", callback_data=f"admin_menu::questions_settings_{admin.button_number}")]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        text=message_text,
                                        parse_mode="HTML",
                                        reply_markup=markup,
                                        message_id=admin.last_message_id)
    admin.save(session)


async def watch_question(update: Update, context: CallbackContext,
                         admin: User, session: Session, data: int):
    admin.admin_cache = json.dumps(None)
    admin.current_question = data
    question = await get_question(admin.current_block, admin.current_question, session)

    if question is None:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])
        message_text = "Вопрос не найден\n\nВозможно, его успел удалить кто-то из других администраторов"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text)
        await questions_block(update, context, admin, session, 0)
        return

    message_text = question.tg_str() + f"\n<i>Ответ: {question.correct_answer}</i>"

    keyboard = [[InlineKeyboardButton(
        text=f"🪶 Редактировать", callback_data=f"admin_menu::question_edit_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"❌ Удалить", callback_data=f"admin_menu::question_delete_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"◀️ Назад", callback_data=f"admin_menu::questions_block_0_{admin.button_number}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(
        chat_id=admin.chat_id,
        text=message_text,
        parse_mode="HTML",
        reply_markup=markup,
        message_id=admin.last_message_id
    )

    admin.save(session)


async def question_delete(update: Update, context: CallbackContext,
                          admin: User, session: Session):
    question = await get_question(admin.current_block, admin.current_question, session)

    message_text = f"Вы уверены, что хотите удалить <b>{question.text}</b> ?"
    keyboard = [[InlineKeyboardButton(
        text=f"Да", callback_data=f"admin_menu::question_delete_confirm_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"Отмена", callback_data=f"admin_menu::questions_block_0_{admin.button_number}")],
    ]

    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        message_id=admin.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    admin.save(session)


async def question_delete_confirm(update: Update, context: CallbackContext,
                                  admin: User, session: Session):
    question = await get_question(admin.current_block, admin.current_question, session)

    message_text = f"❌ Вопрос <b>{question.text}</b> был удалён"
    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        text=message_text,
                                        message_id=admin.last_message_id,
                                        parse_mode="HTML")
    await context.bot.send_sticker(chat_id=admin.chat_id,
                                   sticker=stickers['angry'])

    message = await context.bot.send_message(chat_id=admin.chat_id,
                                             text="Перенаправляю..",
                                             parse_mode="HTML")
    admin.last_message_id = message.message_id
    question.destroy(session)
    await questions_block(update, context, admin, session, 0)
    admin.save(session)


async def questions_add(update: Update, context: CallbackContext,
                        admin: User, session: Session):
    fields = {
        "object_type": "question",
        "title": "❓ Вопрос",
        "cancel_button_query": f"admin_menu::questions_block_0",
        "coroutine_after_finished": questions_block(update, context,
                                                    admin, session, 0),
        "state": "questions_add",
        "stages": [
            {
                "type": "text",
                "enter_text": "Введите <b>📝 Текст </b> вопроса:"
            },
            {
                "type": "list",
                "enter_text": "Введите <b>📌 Варианты ответа </b>\n\n"
                              "<i>Формат ввода:</i>\n\n- первый вариант\n- второй вариант\n- ..."
                              "\n и т.д."
            },
            {
                "type": "text",
                "enter_text": "Введите <b>✅ Правильный вариант ответа </b>"
            },
        ]
    }

    await admin_add_object(update, context, admin, session, fields)
    admin.save(session)


async def question_edit(update: Update, context: CallbackContext,
                        admin: User, session: Session):
    question = await get_question(admin.current_block, admin.current_question, session)

    if question is None:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])
        message_text = "Вопрос не найден\n\nВозможно, его успел удалить кто-то из других администраторов"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text)
        await questions_block(update, context, admin, session, 0)
        return

    message_text = question.tg_str()

    keyboard = [[InlineKeyboardButton(
        text=f"📝 Текст", callback_data=f"admin_menu::question_edit_attr_0_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"📌 Варианты ответа", callback_data=f"admin_menu::question_edit_attr_1_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"✅ Правильный вариант ответа",
            callback_data=f"admin_menu::question_edit_attr_2_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"◀️ Назад", callback_data=f"admin_menu::questions_block_0_{admin.button_number}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    message = await context.bot.edit_message_text(chat_id=admin.chat_id,
                                                  text=message_text,
                                                  parse_mode="HTML",
                                                  reply_markup=markup,
                                                  message_id=admin.last_message_id)

    admin.save(session)


async def question_edit_attr(update: Update, context: CallbackContext,
                             admin: User, session: Session, data: int = None):
    cache = json.loads(admin.admin_cache)
    attr_index = 0
    if data is None:
        is_answered = True
        attr_index = cache['attr']
        cache = None
        pass
    else:
        is_answered = False
        attr_index = data
        cache = {"attr": attr_index}

    question = await get_question(admin.current_block, admin.current_question, session)

    if question is None:
        await error_handler(update, context, admin, session)
        return

    stages = [
        {
            "type": "text",
            "attr": "text",
            "enter_text": "Введите <b>📝 Текст </b> вопроса:"
        },
        {
            "type": "list",
            "attr": "options",
            "enter_text": "Введите <b>📌 Варианты ответа </b>\n\n"
                          "<i>Формат ввода:</i>\n\n- первый вариант\n- второй вариант\n- ..."
                          "\n и т.д."
        },
        {
            "type": "text",
            "attr": "correct_answer",
            "enter_text": "Введите <b>✅ Правильный вариант ответа </b>"
        },
    ]

    fields = {
        "object_type": "question",
        "title": f"<b>📦 {question.text}</b>",
        "cancel_button_query": f"admin_menu::watch_question_{admin.current_question}",
        "coroutine_after_finished": watch_question(update, context,
                                                   admin, session, admin.current_question),
        "state": "question_edit",
        "property": stages[attr_index],
    }

    await admin_edit_object(update, context,
                            admin, session, fields,
                            question, is_answered)
    admin.admin_cache = json.dumps(cache)
    admin.save(session)
