import json
import os
from config import Session
from base.models import Product, Question


def clear_text(text):
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


if __name__ == "__main__":
    session = Session()
    for i in range(6):
        with open(f"block_{i+1}/products.txt", "r") as f:
            body = f.read()
            add_to_products(body, i, session)
