import random
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMedia, InputFile, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from config import Session, BLOCKS_COUNT, smiles_gradient
from base.utils import *
from base.models import *
from commands.bot_utils import button_handler
from commands.products import products_begin
from commands.quizes import begin_quiz

import pandas as pd
import matplotlib.pyplot as plt


@button_handler
async def menu_handler(update: Update, context: CallbackContext,
                       user: User, session: Session, action: str):
    if user.state == "watching_results":
        await context.bot.deleteMessage(chat_id=user.chat_id,
                                        message_id=user.last_message_id)
        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text="Перенаправляю..")
        user.last_message_id = message.message_id
        user.state = "main_menu"

    action_fields = action.split("_")

    if action == "menu::main":
        await main_menu(update, context, user, session)
    elif action == "menu::results":
        await watch_results(update, context, user, session)
    elif action == "menu::choose_test":
        await choose_test(update, context, user, session)
    elif (len(action_fields) > 2
          and action_fields[0] == "menu::study"
          and action_fields[1] == "block"
          and action_fields[2].isnumeric()):

        await study_block(update, context, user, session, int(action_fields[2]))

    elif (len(action_fields) > 2
          and action_fields[0] == "menu::test"
          and action_fields[1] == "block"
          and action_fields[2].isnumeric()):

        await test_block(update, context, user, session, int(action_fields[2]))

    elif action == "menu::choose_study_block":
        await choose_study_block(update, context, user, session)
    elif action == "menu::continue_study":
        await continue_study(update, context, user, session)
    elif action == "menu::more":
        await more(update, context, user, session)
    user.save(session)


async def main_menu(update: Update, context: CallbackContext,
                    user: User, session: Session):
    if user.state == "quiz_solving":
        message_text = "У вас начат тест. Сначала закончите его"
        user.last_message_id = await context.bot.send_message(
            chat_id=user.chat_id, text=message_text)
        user.save(session)
        return

    message_text = f"<b>{random.choice('📕📗📘📙📚📒')} Меню</b>\n\n"
    if user.max_block == BLOCKS_COUNT:
        message_text += ("🏁 Вы завершили все блоки\n\n"
                         "Можете пройти обучение ещё раз или улучшить результаты тестов")
    else:
        message_text += (f"📌 Вы завершили {user.max_block} из {BLOCKS_COUNT} блоков \n\n"
                         f"Можете улучшить текущие результаты или пройти оставшийся материал")
    keyboard = []
    if user.current_block != BLOCKS_COUNT:
        keyboard.append([InlineKeyboardButton("⏯ Продолжить",
                                              callback_data=f'menu::continue_study_{user.button_number}')])
    keyboard += [[InlineKeyboardButton("📊 Результаты",
                                       callback_data=f'menu::results_{user.button_number}')],
                 [InlineKeyboardButton("✍️ Пройти обучение",
                                       callback_data=f'menu::choose_study_block_{user.button_number}')],
                 [InlineKeyboardButton("🔄 Пройти тесты",
                                       callback_data=f'menu::choose_test_{user.button_number}')],
                 [InlineKeyboardButton("⚙️ Ещё",
                                       callback_data=f'menu::more_{user.button_number}')]]

    markup = InlineKeyboardMarkup(keyboard)

    if user.state == "main_menu":
        await context.bot.edit_message_text(chat_id=user.chat_id,
                                            message_id=user.last_message_id,
                                            text=message_text,
                                            reply_markup=markup,
                                            parse_mode="HTML")
    else:
        user.state = "main_menu"

        message = await context.bot.send_message(chat_id=user.chat_id,
                                                 text=message_text,
                                                 reply_markup=markup,
                                                 parse_mode="HTML")
        user.last_message_id = message.message_id

    user.save(session)


def result_string(result):
    correct, wrong, not_started = result
    count = len(correct) + len(wrong) + len(not_started)
    percent = int(round(float(len(correct)) / count * 100, 0))
    smile = smiles_gradient[percent * (len(smiles_gradient) - 1) // 100]
    string = (f"- <b>{percent} % {smile}</b>\n"
              f"- <i>Правильно: {len(correct)} / {count}</i>\n")
    if len(not_started) > 0:
        string += f"- <i>Пропущено: {len(not_started)} / {count}</i>\n"
    # if len(wrong) > 0:
    # string += f"- <i>Неправильно: {len(wrong)} / {count}</i>\n"
    return string


async def watch_results(update: Update, context: CallbackContext,
                        user: User, session: Session):
    message_text = f"<b>📊 Ваши результаты:</b>\n\n"
    message_text += f"📌 Среднее - average %\n\n"
    results = await get_tests_results(user, session)
    results_to_plot = []

    sum_percent = 0
    count_present = 0

    for i in range(BLOCKS_COUNT):
        if results[i] is None:
            message_text += f"<b>🔒 Тест {i + 1} </b>"
            message_text += "- <i>не начат</i>\n"
            results_to_plot.append({"Правильно": 0, "Пропущено": 0})
        else:
            message_text += f"<b>Тест {i + 1} </b>"
            message_text += f"{result_string(results[i])}"
            # collecting data for the plot
            correct, wrong, not_started = results[i]
            count = len(correct) + len(wrong) + len(not_started)
            corr_percent = int(round(float(len(correct)) / count * 100, 0))
            ignored_percent = int(round(float(len(not_started)) / count * 100, 0))
            results_to_plot.append({"Правильно": corr_percent, "Пропущено": ignored_percent})

            sum_percent += corr_percent
            count_present += 1

        message_text += "\n"
    if count_present > 0:
        average = sum_percent // count_present
        message_text = message_text.replace("average", f"{average}")
    else:
        message_text = message_text.replace(f"📌 Среднее - average %\n\n", "")

    keyboard = []
    if user.current_block != BLOCKS_COUNT:
        keyboard.append([InlineKeyboardButton("⏯ Продолжить",
                                              callback_data=f'menu::continue_study_{user.button_number}')])
    keyboard += [[InlineKeyboardButton(
        "✍️ Пройти обучение", callback_data=f'menu::choose_study_block_{user.button_number}')],
        [InlineKeyboardButton(
            "🔄 Пройти тесты", callback_data=f'menu::choose_test_{user.button_number}')],
        [InlineKeyboardButton(
            "◀️ Назад", callback_data=f'menu::main_{user.button_number}')]]

    markup = InlineKeyboardMarkup(keyboard)

    # plotting
    df = pd.DataFrame(results_to_plot)
    df.plot(kind='bar', stacked=True, color=['limegreen', 'lightgrey'])
    plt.xlabel('Номер теста', fontsize=18, labelpad=4)
    plt.ylabel('% выполнения', fontsize=18)
    plt.gca().set_ylim([0, 100])
    plt.legend(loc=0, prop={'size': 14})
    plt.legend(loc=1, prop={'size': 14})
    plt.box(False)

    plt.xticks(range(BLOCKS_COUNT), labels=[str(i + 1) for i in range(BLOCKS_COUNT)],
               fontsize=14, rotation=0)
    plt.yticks(fontsize=14)
    plt.title('Ваши результаты', fontsize=18, pad=22)
    plt.tight_layout()
    # convert the plot to bytes
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image = InputFile(buf)
    await context.bot.deleteMessage(chat_id=user.chat_id,
                                    message_id=user.last_message_id)
    message = await context.bot.send_photo(chat_id=user.chat_id, photo=image,
                                           caption=message_text, parse_mode='HTML',
                                           reply_markup=markup)
    user.last_message_id = message.message_id
    user.state = "watching_results"
    user.save(session)


async def choose_test(update: Update, context: CallbackContext,
                      user: User, session: Session):
    message_text = f"<b>Выберите тест:</b>\n\n"
    keyboard = []
    for i in range(BLOCKS_COUNT):
        button_text = f"Тест {i + 1}"
        if user.max_block - 1 < i:
            button_text = "🔒 " + button_text
        else:
            pass
            # button_text += str(await get_test_results(user, i))

        keyboard.append([InlineKeyboardButton(
            button_text, callback_data=f'menu::test_block_{i}_{user.button_number}')], )

    keyboard.append([InlineKeyboardButton(
        "Назад", callback_data=f'menu::main_{user.button_number}')])

    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        message_id=user.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    user.state = "main_menu"
    user.save(session)


async def test_block(update: Update, context: CallbackContext,
                     user: User, session: Session, block: int):
    if user.max_block > block:
        user.current_block = block
        await begin_quiz(update, context, user, session)
    else:
        user.button_number -= 1

    user.save(session)


async def choose_study_block(update: Update, context: CallbackContext,
                             user: User, session: Session):
    message_text = f"<b>Выберите блок:</b>\n\n"
    keyboard = []
    for i in range(BLOCKS_COUNT):
        button_text = f"Блок {i + 1}"
        if user.max_block < i:
            button_text = "🔒 " + button_text
        keyboard.append([InlineKeyboardButton(
            button_text, callback_data=f'menu::study_block_{i}_{user.button_number}')], )

    keyboard.append([InlineKeyboardButton(
        "Назад", callback_data=f'menu::main_{user.button_number}')])

    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=user.chat_id,
                                        message_id=user.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    user.state = "main_menu"
    user.save(session)


async def study_block(update: Update, context: CallbackContext,
                      user: User, session: Session, block: int):
    if user.max_block >= block:
        user.current_block = block
        user.current_product = 0
        await products_begin.__wrapped__(
            update, context, user, session)
    else:
        user.button_number -= 1

    user.save(session)


async def continue_study(update: Update, context: CallbackContext,
                         user: User, session: Session):
    if user.current_block < BLOCKS_COUNT:
        await products_begin.__wrapped__(update, context, user, session)


async def more(update: Update, context: CallbackContext,
               user: User, session: Session):
    message_text = ("🔐 <b>Панель администратора </b>"
                    f"\n\nВведите 🔑 ключ администратора для входа"
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
    print(user)
    user.save(session)
