def clear_option_text(text):
    text = text[text.find(" ") + 1:]
    return text


def clear_text(text):
    if len(text) == 0:
        return

    text = text.replace("-", "", 1)
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
    new_arr = []
    for i, txt in enumerate(arr):
        arr[i] = clear_text(txt)
        if arr[i] in ["", "- ", "-"]:
            continue
        new_arr.append(arr[i])
    return new_arr
