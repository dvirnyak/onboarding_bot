from io import BytesIO

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from telegram import InputFile

from base.models import User, Record, Question
import base.utils
from config import BLOCKS_COUNT, Session


async def results_image(results, title) -> InputFile:
    results_to_plot = []

    for i in range(BLOCKS_COUNT):
        if i >= len(results):
            results_to_plot.append({"Правильно": 0, "Пропущено": 0})
        else:
            results_to_plot.append({"Правильно": results[i]['correct_percent'],
                                    "Пропущено": results[i]['ignored_percent']})

    df = pd.DataFrame(results_to_plot)

    df.plot(kind='bar', stacked=True, color=['limegreen', 'lightgrey'])
    plt.title(title, fontsize=18, pad=22)
    plt.xlabel('Номер теста', fontsize=18, labelpad=4)
    plt.ylabel('% выполнения', fontsize=18)
    plt.gca().set_ylim([0, 100])
    plt.legend(loc=0, prop={'size': 14})
    plt.legend(loc=1, prop={'size': 14})
    plt.box(False)
    plt.xticks(range(BLOCKS_COUNT), labels=[str(i + 1) for i in range(BLOCKS_COUNT)],
               fontsize=14, rotation=0)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    # convert the plot to bytes
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image = InputFile(buf)

    return image


async def user_blocks_statistics(session: Session) -> InputFile:
    max_blocks = session.query(User.max_block).all()
    max_blocks = [i[0] for i in max_blocks]
    max_blocks = [max_blocks.count(i) for i in range(BLOCKS_COUNT + 1)]

    df = pd.DataFrame(max_blocks)

    df.plot(kind='bar', legend=None, grid=False,
            color="orange")

    plt.title("Прогресс пользователей бота", fontsize=18, pad=22)
    plt.xlabel('Число пройденных блоков', fontsize=18, labelpad=4)
    plt.ylabel('Количество пользователей', fontsize=18)

    plt.box(False)
    plt.xticks(np.arange(0, BLOCKS_COUNT + 1),
               labels=[str(i) for i in range(0, BLOCKS_COUNT + 1)],
               fontsize=14, rotation=0)
    plt.yticks(range(max(max_blocks) + 1),
               labels=[str(i) for i in range(max(max_blocks) + 1)],
               fontsize=14)
    # ax.set_ylim([0, df.max()])

    plt.tight_layout()

    # convert the plot to bytes
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image = InputFile(buf)

    return image


async def results_statistics_image(session: Session) -> InputFile:
    users = session.query(User).all()
    averages = []
    max_avg_count = 0
    for user in users:
        results, average = await base.utils.get_tests_results(user, session)
        averages.append(average)
        max_avg_count = max(max_avg_count, averages.count(average))

    ax = plt.figure().gca()
    df = pd.DataFrame(averages)

    df.hist(legend=None, grid=False)

    plt.title("Результаты пользователей бота", fontsize=18, pad=22)
    plt.xlabel('Средний %', fontsize=18, labelpad=4)
    plt.ylabel('Количество пользователей', fontsize=18)

    plt.box(False)
    plt.xticks(fontsize=14)
    plt.yticks(range(max_avg_count + 1),
               labels=[str(i) for i in range(max_avg_count + 1)],
               fontsize=14)
    plt.xlim([0, 100])

    plt.tight_layout()

    # convert the plot to bytes
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image = InputFile(buf)

    return image


async def panel_statistics() -> InputFile:
    pass

async def question_statistics(session: Session) -> InputFile:
    pass
