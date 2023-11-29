from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, \
    KeyboardButton
from telegram.ext import CallbackContext

from commands.admin_commands import admin
from config import stickers, smiles_gradient
from base.utils import get_question
from base.models import *
from config import Session, BLOCKS_COUNT
from commands.bot_utils import error_handler, button_handler
from datetime import datetime, timedelta

QUIZ_TIME = 301
INTERVAL = 10


@button_handler
async def quiz_solving(update: Update, context: CallbackContext,
                       user: User, session: Session, action: str):
    if action == "quiz::start":
        user.last_quiz_started = datetime.now()
        job = context.job_queue.run_repeating(update_time_in_message,
                                              interval=INTERVAL, first=0,
                                              data=[user.chat_id, user.quiz_index])
        await context.job_queue.start()

        user.state = "quiz_solving"
        user.current_question = 0
        action = "quiz::show_question"

    action_fields = action.split("_")

    if len(action_fields) >= 1 and action_fields[0] == "quiz::submit":
        answer = action_fields[1]
        if not answer.isnumeric():
            await error_handler(update, context, user, session)
            return

        await submit_answer(update, context, user, session, int(answer))
        action = "quiz::show_question"

    if action == "quiz::back" and user.current_question > 0:
        user.current_question -= 1
        user.records[-1].destroy(session)
        action = "quiz::show_question"

    if action == "quiz::show_question":
        questions = session.query(Question).filter_by(block=user.current_block).all()

        if len(questions) <= user.current_question:
            await confirm(update, context, user, session)
            user.save(session)
            return

        await show_question(user, context, session)

    if action == "quiz::finish":
        await end_quiz(user, context, session)


async def confirm(update: Update, context: CallbackContext,
                  user: User, session: Session):
    message_text = "<b>📋 Ваши ответы:</b>\n\n"
    i = 0
    for record in user.records:
        if record.quiz_index == user.quiz_index:
            message_text += f"{i + 1}) {record.answer}\n"
            i += 1
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f'quiz::finish_{user.button_number}')],
        [InlineKeyboardButton("◀ Назад", callback_data=f'quiz::back_{user.button_number}')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        text=message_text,
                                        message_id=user.last_message_id,
                                        reply_markup=markup,
                                        parse_mode="HTML")


async def begin_quiz(update: Update, context: CallbackContext,
                     user: User, session: Session):
    user.state = "quiz_start_awaiting"

    time_str = ""
    if (QUIZ_TIME - 1) // 60 != 0:
        time_str += f"{(QUIZ_TIME - 1) // 60} минут"
    if (QUIZ_TIME - 1) % 60 != 0:
        time_str += " {(QUIZ_TIME - 1) % 60} секунд"

    # send actual message
    message_text = (f"<b>Тест {user.current_block + 1}</b>\n\n"
                    f"⏳ Вам будет дано {time_str} \n\n"
                    f"Когда будете готовы, нажмите <b>▶️ Начать</b>\n"
                    f"Удачи!")
    keyboard = [
        [InlineKeyboardButton("▶️ Начать", callback_data=f'quiz::start_{user.button_number}')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(chat_id=user.chat_id, text=message_text,
                                             reply_markup=markup, parse_mode='HTML')
    user.last_message_id = message.message_id
    user.save(session)


async def end_quiz(user: User, context: CallbackContext, session: Session()):
    await admin.notify(context, user, session, "quiz_finished")
    await show_results(user, context, session)

    user.quiz_index += 1
    user.current_block += 1
    user.current_product = 0

    if user.max_block == BLOCKS_COUNT - 1 \
            and user.current_block == BLOCKS_COUNT:
        await admin.notify(context, user, session, "all_quizes_finished")
        message_text = ("🥳 Поздравляю!\n\n✔️ Вы усвоили весь материал и прошли все тесты\n\n"
                        "При необходимости это можно сделать ещё раз через меню")
        await context.bot.send_message(chat_id=user.chat_id,
                                       text=message_text)
        await context.bot.send_sticker(chat_id=user.chat_id,
                                       sticker=stickers["chill"])

    user.max_block = max(user.current_block, user.max_block)
    user.state = "quiz_finished"
    if not (context.job is None):
        context.job.schedule_removal()

    user.save(session)


async def show_results(user: User, context: CallbackContext, session: Session):
    mistaken = []
    right = []
    correct_count = 0
    not_answered = 0
    count = 0
    # retrieve data
    for record in user.records:
        if record.quiz_index == user.quiz_index:
            if record.is_correct:
                correct_count += 1
                right.append(record.question.text)
            elif record.answer == -1:
                not_answered += 1
            else:
                mistaken.append(record.question.text)
            count += 1
    # form a message

    message_text = f"<b>Тест {user.current_block + 1} завершён\n"
    percent = 0
    if count != 0:
        percent = int(round(float(correct_count) / float(count) * 100, 0))
    smile = smiles_gradient[percent * (len(smiles_gradient) - 1) // 100]

    message_text += f"{smile} {percent} %</b>\n\n"
    # sugar
    if correct_count != count:
        message_text += f"Вы ответили верно на {correct_count} из {count} вопросов."
    else:
        message_text += "Вы ответили верно на все вопросы"

    if len(mistaken) > 0:
        message_text += f"\n\nВ этих вопросах вы ошиблись:\n- " + "\n- ".join(mistaken[:5])

    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        message_id=user.last_message_id,
                                        text=message_text,
                                        parse_mode='HTML')
    keyboard = [
        [KeyboardButton("Продолжить")],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    user.last_msg_has_keyboard = True

    sticker = stickers['respect'] if percent >= 50 else stickers['sad']
    sticker = stickers['congratulate'] if percent == 100 else sticker
    await context.bot.send_sticker(chat_id=user.chat_id,
                                   sticker=sticker,
                                   reply_markup=markup)


async def update_time_in_message(context: CallbackContext):
    chat_id = context.job.data[0]
    quiz_index = context.job.data[1]

    session = Session()
    user = session.query(User).with_for_update().filter_by(chat_id=chat_id).first()
    if user is None:
        return
    if user.quiz_index != quiz_index:
        context.job.schedule_removal()
        return

    questions = session.query(Question).filter_by(block=user.current_block).all()
    num_questions = len(questions)
    if (datetime.now() >= user.last_quiz_started
            + timedelta(seconds=QUIZ_TIME - 1)):
        while num_questions > user.current_question:
            await submit_answer(None, context, user, session, -1)

        await end_quiz(user, context, session)
        return

    if user.current_question < num_questions:
        await show_question(user, context, session)
    user.save(session)


async def show_question(user: User, context: CallbackContext, session: Session):
    questions = session.query(Question).filter_by(block=user.current_block).all()
    question = await get_question(user.current_block, user.current_question, session)

    # setting up left time
    remaining_time = (user.last_quiz_started + timedelta(seconds=QUIZ_TIME)
                      - datetime.now())
    remaining_time_str = f"⏳Осталось: {remaining_time.seconds // 60}:{(remaining_time.seconds % 60):02d}"

    message_text = (f"<b>Вопрос {user.current_question + 1} / {len(questions)}</b>\n"
                    f"\n{remaining_time_str}\n\n")
    message_text += question.tg_str()
    # collecting options
    keyboard = []
    options = json.loads(question.options)
    for i in range(len(options)):
        keyboard.append(
            [InlineKeyboardButton(f"{i + 1}",
                                  callback_data=f'quiz::submit_{i + 1}_{user.button_number}')],
        )
    if user.current_question != 0:
        keyboard.append(
            [InlineKeyboardButton(f"◀ Назад",
                                  callback_data=f'quiz::back_{user.button_number}')],
        )
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        text=message_text, message_id=user.last_message_id,
                                        reply_markup=markup, parse_mode='HTML')
    user.save(session)


async def submit_answer(update: Update, context: CallbackContext,
                        user: User, session: Session, answer: int):
    questions = session.query(Question).filter_by(block=user.current_block).all()
    if len(questions) <= user.current_question:
        return error_handler(update, context, user, session)
    question = questions[user.current_question]

    record = Record(user=user, question=question, answer=answer,
                    is_correct=(answer == question.correct_answer),
                    block=user.current_block, quiz_index=user.quiz_index)
    session.add(record)
    user.current_question += 1
