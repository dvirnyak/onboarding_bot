from commands.admin_commands.object_managing import *
from config import stickers
from base.utils import *
from base.models import *
from commands.bot_utils import form_paged_message, choose_block_template, get_image, error_handler

page_size = 5


async def products_settings(update: Update, context: CallbackContext,
                            admin: User, session: Session):
    admin.admin_current_page = 0
    admin.current_block = 0
    start_message = f"<b>Выберите продуктовый блок:</b>\n\n"
    button_text = "Блок"
    block_query = f'admin_menu::products_block_chosen'
    back_query = f'admin_menu::menu_{admin.button_number}'

    await choose_block_template(update, context,
                                admin, session,
                                start_message, button_text,
                                block_query, back_query)
    admin.save(session)


async def products_block(update: Update, context: CallbackContext,
                         admin: User, session: Session, data: int):
    admin.admin_cache = json.dumps(None)
    if data == 1:
        admin.admin_current_page -= 1
    elif data == 2:
        admin.admin_current_page += 1

    async def message_maker(products, i):
        product = products[i]
        product_text = f"- <b>{product}</b>\n\n"
        product_text = ""

        return product_text

    async def button_maker(products, i):
        button_text = f"{products[i]}"
        query = f"admin_menu::watch_product_{i}_{admin.button_number}"
        return button_text, query

    products = session.query(Product).filter_by(block=admin.current_block).all()

    backward_query = f'admin_menu::products_block_1_{admin.button_number}'
    forward_query = f'admin_menu::products_block_2_{admin.button_number}'

    start_message = (f"<b>🛍  Продукты</b>\n\n<i>Блок {admin.current_block + 1}\n\n</i>"
                     "📃 Чтобы посмотреть подробнее, нажмите на "
                     "соответсвующую кнопку\n\n")

    message_text, keyboard = await form_paged_message(products, message_maker,
                                                      button_maker, page_size,
                                                      admin.admin_current_page,
                                                      backward_query, forward_query)

    message_text = start_message + message_text

    keyboard += [[InlineKeyboardButton(
        text=f"🆕 Добавить", callback_data=f"admin_menu::products_add_{admin.button_number}")]]

    keyboard += [[InlineKeyboardButton(
        text=f"◀️ Назад", callback_data=f"admin_menu::products_settings_{admin.button_number}")]]
    markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.edit_message_text(chat_id=admin.chat_id,
                                                  text=message_text,
                                                  parse_mode="HTML",
                                                  reply_markup=markup,
                                                  message_id=admin.last_message_id)
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = False
    admin.save(session)


async def watch_product(update: Update, context: CallbackContext,
                        admin: User, session: Session, data: int):
    admin.current_product = data
    product = await get_product(admin.current_block, admin.current_product, session)

    if product is None:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])
        message_text = "Продукт не найден\n\nВозможно, его успел удалить кто-то из других администраторов"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text)
        await products_block(update, context, admin, session, 0)
        return

    message_text = product.tg_str()
    image = await get_image(product.image_path, admin, context)

    keyboard = [[InlineKeyboardButton(
        text=f"🪶 Редактировать", callback_data=f"admin_menu::product_edit_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"❌ Удалить", callback_data=f"admin_menu::product_delete_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"◀️ Назад", callback_data=f"admin_menu::products_block_0_{admin.button_number}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.deleteMessage(chat_id=admin.chat_id,
                                    message_id=admin.last_message_id)
    message = await context.bot.send_photo(chat_id=admin.chat_id,
                                           caption=message_text,
                                           parse_mode="HTML",
                                           photo=image,
                                           reply_markup=markup)
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = True

    admin.save(session)


async def products_add(update: Update, context: CallbackContext,
                       admin: User, session: Session):
    fields = {
        "object_type": "product",
        "title": "📦 Продукт",
        "cancel_button_query": f"admin_menu::products_block_0",
        "coroutine_after_finished": products_block(update, context,
                                                   admin, session, 0),
        "state": "products_add",
        "stages": [
            {
                "type": "text",
                "enter_text": "Введите <b>🚩 Название</b> продукта:"
            },
            {
                "type": "text",
                "enter_text": "Введите <b>📝 Описание</b> продукта:"
            },
            {
                "type": "text",
                "enter_text": "Введите <b>💵 Цену</b> Продукта:"
            },
            {
                "type": "list",
                "enter_text": "Введите <b>🥂 Продукты, с которым совмещают данный</b>\n\n"
                              "<i>Формат ввода:</i>\n\n- первый продукт\n- второй продукт\n- ..."
                              "\n и т.д."
            },
            {
                "type": "list",
                "enter_text": "Введите <b>✨ Эффекты</b> Продукта\n\n"
                              "<i>Формат ввода:</i>\n\n- первый эффект\n- второй эффект\n- ..."
                              "\n и т.д."
            },
            {
                "type": "image",
                "enter_text": "Пришлите 🖼 Фото Продукта:"
            },
        ]
    }

    await admin_add_object(update, context, admin, session, fields)
    admin.save(session)


async def product_delete(update: Update, context: CallbackContext,
                         admin: User, session: Session):
    product = await get_product(admin.current_block, admin.current_product, session)

    message_text = f"Вы уверены, что хотите удалить <b>{product.title}</b> ?"
    keyboard = [[InlineKeyboardButton(
        text=f"Да", callback_data=f"admin_menu::product_delete_confirm_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"Отмена", callback_data=f"admin_menu::products_block_0_{admin.button_number}")],
    ]

    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(chat_id=admin.chat_id,
                                        message_id=admin.last_message_id,
                                        text=message_text,
                                        reply_markup=markup,
                                        parse_mode="HTML")
    admin.save(session)


async def product_delete_confirm(update: Update, context: CallbackContext,
                                 admin: User, session: Session):
    product = await get_product(admin.current_block, admin.current_product, session)

    message_text = f"❌ Продукт <b>{product.title}</b> был удалён"
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
    product.destroy(session)
    await products_block(update, context, admin, session, 0)
    admin.save(session)


async def product_edit(update: Update, context: CallbackContext,
                       admin: User, session: Session):
    product = await get_product(admin.current_block, admin.current_product, session)

    if product is None:
        await context.bot.send_sticker(chat_id=admin.chat_id,
                                       sticker=stickers['error'])
        message_text = "Продукт не найден\n\nВозможно, его успел удалить кто-то из других администраторов"
        await context.bot.send_message(chat_id=admin.chat_id,
                                       text=message_text)
        await products_block(update, context, admin, session, 0)
        return

    message_text = product.tg_str()
    image = await get_image(product.image_path, admin, context)

    keyboard = [[InlineKeyboardButton(
        text=f"🚩 Название", callback_data=f"admin_menu::product_edit_attr_0_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"📝 Описание", callback_data=f"admin_menu::product_edit_attr_1_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"💵 Цена", callback_data=f"admin_menu::product_edit_attr_2_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"🥂 Совмещают с", callback_data=f"admin_menu::product_edit_attr_3_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"✨ Эффекты", callback_data=f"admin_menu::product_edit_attr_4_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"🖼 Картинка", callback_data=f"admin_menu::product_edit_attr_5_{admin.button_number}")],
        [InlineKeyboardButton(
            text=f"◀️ Назад", callback_data=f"admin_menu::products_block_0_{admin.button_number}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.deleteMessage(chat_id=admin.chat_id,
                                    message_id=admin.last_message_id)
    message = await context.bot.send_photo(chat_id=admin.chat_id,
                                           caption=message_text,
                                           parse_mode="HTML",
                                           photo=image,
                                           reply_markup=markup)
    admin.last_message_id = message.message_id
    admin.last_msg_is_photo = True

    admin.save(session)


async def product_edit_attr(update: Update, context: CallbackContext,
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

    product = await get_product(admin.current_block, admin.current_product, session)

    if product is None:
        await error_handler(update, context, admin, session)
        return

    stages = [
        {
            "type": "text",
            "attr": "title",
            "enter_text": "Введите <b>🚩 Название</b> продукта:"
        },
        {
            "type": "text",
            "attr": "description",
            "enter_text": "Введите <b>📝 Описание</b> продукта:"
        },
        {
            "type": "text",
            "attr": "price",
            "enter_text": "Введите <b>💵 Цену</b> Продукта:"
        },
        {
            "type": "list",
            "attr": "together",
            "enter_text": "Введите <b>🥂 Продукты, с которым совмещают данный</b>\n\n"
                          "<i>Формат ввода:</i>\n\n- первый продукт\n- второй продукт\n- ..."
                          "\n и т.д."
        },
        {
            "type": "list",
            "attr": "effects",
            "enter_text": "Введите <b>✨ Эффекты</b> Продукта\n\n"
                          "<i>Формат ввода:</i>\n\n- первый эффект\n- второй эффект\n- ..."
                          "\n и т.д."
        },
        {
            "type": "image",
            "attr": "image_path",
            "enter_text": "Пришлите 🖼 Фото Продукта:"
        },
    ]

    fields = {
        "object_type": "product",
        "title": f"<b>📦 {product.title}</b>",
        "cancel_button_query": f"admin_menu::watch_product_{admin.current_product}",
        "coroutine_after_finished": watch_product(update, context,
                                                  admin, session, admin.current_product),
        "state": "product_edit",
        "property": stages[attr_index],
    }

    await admin_edit_object(update, context,
                            admin, session, fields,
                            product, is_answered)
    admin.admin_cache = json.dumps(cache)
    admin.save(session)
