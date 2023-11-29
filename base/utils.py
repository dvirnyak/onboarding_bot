from sqlalchemy import desc
from telegram import InputFile

import base
from base import images
from base.models import User, Product, Record, Question
from config import BLOCKS_COUNT, Session, smiles_gradient
import pandas as pd


async def get_user(update, session) -> User:
    chat_id = update.effective_chat.id
    user = (
        session.query(User).with_for_update().filter_by(chat_id=chat_id).first()
    )
    if user is None:
        user = User(chat_id=chat_id,
                    first_name=update.effective_chat.first_name,
                    last_name=update.effective_chat.last_name)
        user.save(session)

    return user


async def get_product(block, index, session) -> Product | None:
    products = (
        session.query(Product).filter_by(block=block).all())
    if products is None or len(products) <= index:
        return None

    return products[index]


async def get_question(block, index, session) -> Question | None:
    questions = (
        session.query(Question).filter_by(block=block).all())
    if questions is None or len(questions) <= index:
        return None

    return questions[index]


async def get_test_results(user: User, session: Session, block: int) -> dict:
    if user.max_block < block:
        return None

    # getting the latest attempt
    quiz_indexes = session.query(Record.quiz_index).filter_by(
        user=user, block=block
    ).all()
    if len(quiz_indexes) == 0:
        return None
    max_quiz_index = max(quiz_indexes)[0]

    wrong_records = session.query(Record).filter_by(
        user=user, block=block, quiz_index=max_quiz_index,
        is_correct=False
    ).filter(Record.answer != -1).all()

    not_started_records = session.query(Record).filter_by(
        user=user, block=block, quiz_index=max_quiz_index
    ).filter(Record.answer == -1).all()

    correct_records = session.query(Record).filter_by(
        user=user, block=block, quiz_index=max_quiz_index,
        is_correct=True
    ).all()

    count = (len(correct_records) + len(not_started_records)
             + len(wrong_records))
    percent = 0 if count == 0 else (
        int(round(float(len(correct_records)) / count * 100, 0)))
    ignored_percent = 0 if count == 0 else (
        int(round(float(len(not_started_records)) / count * 100, 0)))
    wrong_percent = 0 if count == 0 else (
        int(round(float(len(wrong_records)) / count * 100, 0)))

    answer = {"correct_records": correct_records,
              "wrong_records": wrong_records,
              "ignored_records": not_started_records,
              "correct_percent": percent,
              "correct_count": len(correct_records),
              "ignored_count": len(not_started_records),
              "wrong_count": len(wrong_records),
              "count": count,
              "ignored_percent": ignored_percent,
              "wrong_percent": wrong_percent,
              "present": count != 0,
              "attempt": len(set(quiz_indexes))}

    return answer


async def get_tests_results(user: User, session: Session, block: int = None):
    if not (block is None):
        return await get_tests_results(user, session, block)

    results = []
    sum_percent = 0
    count = 0
    for i in range(BLOCKS_COUNT):
        result = await get_test_results(user, session, i)
        if result is not None:
            results.append(result)
            sum_percent += results[i]['correct_percent']
            count += 1

    average = 0 if count == 0 else sum_percent // count

    return results, average


def result_string(result):
    percent = result['correct_percent']
    smile = smiles_gradient[percent * (len(smiles_gradient) - 1) // 100]
    string = (f"- <b>{percent} % {smile}</b>\n"
              f"- <i>Правильно: {result['correct_count']} / "
              f"{result['count']}</i>\n")
    if result['ignored_count'] > 0:
        string += (f"- <i>Пропущено: {result['correct_count']} / "
                   f"{result['count']}</i>\n")

    return string


async def get_formatted_user_results(user, session, admin_asked=False):
    message_text = f"<b>📊 Ваши результаты:</b>\n\n" \
        if not admin_asked else f"<b>📊 Результаты {user.tg_str()}:</b>\n\n"

    message_text += f"📌 Среднее - average %\n\n"
    results, average = await get_tests_results(user, session)

    for i in range(BLOCKS_COUNT):
        if i >= len(results):
            message_text += f"<b>🔒 Тест {i + 1} </b>" if not admin_asked else ""
            message_text += "- <i>не начат</i>\n" if not admin_asked else ""
        else:
            message_text += f"<b>Тест {i + 1} </b>"
            message_text += f"{result_string(results[i])}"
            if admin_asked and results[i]['attempt'] > 1:
                message_text += f"<i>- {results[i]['attempt']} попытки</i>\n"

        message_text += "\n"

    if len(results) > 0:
        message_text = message_text.replace("average", f"{average}")
    elif len(results) == 0:
        message_text = message_text.replace(f"📌 Среднее - average %\n\n", "")
        if admin_asked:
            message_text = message_text.replace("\n\n", "", 3)
            message_text += "🚫 <i>Не приступал к тестам</i>" if admin_asked else ""

    # plotting
    title = "Ваши результаты" if not admin_asked \
        else (f"Результаты {user.first_name} "
              f"{user.last_name if not user.last_name is None else ''}")

    image = await images.results_image(results, title)

    return message_text, image
