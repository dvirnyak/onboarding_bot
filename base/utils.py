from typing import Any

from sqlalchemy import desc

from base.models import User, Product, Record, Question
from config import BLOCKS_COUNT, Session
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


async def get_test_results(user: User, session: Session, block: int):
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

    return correct_records, wrong_records, not_started_records


async def get_tests_results(user: User, session: Session, block: int = None):
    if not (block is None):
        return await get_tests_results(user, session, block)

    results = []
    for i in range(BLOCKS_COUNT):
        results.append(await get_test_results(user, session, i))

    return results
