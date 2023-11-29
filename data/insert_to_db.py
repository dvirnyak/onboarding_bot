import json

from config import Session, PROJECT_PATH
from base.models import Product, Question


def clear_option_text(text):
    text = text[text.find(" ") + 1:]
    return text


def clear_text(text):
    text = text.replace(")", ") ").replace(" )", ")")
    # Fool defense
    while text != text.replace("\n\n\n", "\n\n"):
        text = text.replace("\n\n\n", "\n\n")

    while text != text.replace(" \n", "\n"):
        text = text.replace(" \n", "\n")

    while text != text.replace(" " * 2, " "):
        text = text.replace(" " * 2, " ")

    while text != text.replace("," * 2, ","):
        text = text.replace("," * 2, ",")

    while text != text.replace(", ,", ","):
        text = text.replace(", ,", ",")

    while len(text) > 0 and text[-1] in [' ', ',', '\n']:
        text = text[:-1]

    while len(text) > 0 and text[0] in [' ', ',', '\n']:
        text = text[1:]

    return text


def clear_text_arr(arr):
    for i, txt in enumerate(arr):
        arr[i] = clear_text(txt)
    return arr


def add_to_products(body, block, session):
    body = clear_text(body)
    product_txts = clear_text_arr(list(body.split("\n\n")))

    for product_txt in product_txts:
        product_txt = clear_text(product_txt)
        fields_array = product_txt.split("\n")

        # clearing
        fields_array[3] = clear_text(fields_array[3])
        together = clear_text_arr(fields_array[3].split(","))

        fields_array[4] = clear_text(fields_array[4])
        effects = clear_text_arr(fields_array[4].split(","))

        product = Product(title=fields_array[0],
                          description=fields_array[1],
                          price=fields_array[2],
                          together=json.dumps(together),
                          effects=json.dumps(effects),
                          image_path=fields_array[5],
                          block=block)

        product.save(session)


def add_to_questions(body, block, session):
    body = clear_text(body)
    question_txts = clear_text_arr(list(body.split("\n\n")))

    for question_txt in question_txts:
        question_txt = clear_text(question_txt)
        fields_array = question_txt.split("\n")

        num_options = len(fields_array) - 2
        options = []

        for i in range(num_options):
            options.append(clear_option_text(fields_array[1 + i]))

        correct_answer = int(fields_array[-1][-1])

        question = Question(text=fields_array[0],
                            options=json.dumps(options),
                            correct_answer=correct_answer,
                            block=block)

        question.save(session)


def run_insertions():
    session = Session()
    for i in range(6):
        with open(PROJECT_PATH + "/data/" + f"block_{i + 1}/products.txt", "r") as f:
            body = f.read()
            add_to_products(body, i, session)

        with open(PROJECT_PATH + "/data/" + f"block_{i + 1}/questions.txt", "r") as f:
            body = f.read()
            add_to_questions(body, i, session)

