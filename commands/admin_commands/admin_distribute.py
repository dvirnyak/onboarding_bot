from commands.admin_commands.admin_menu import *
from commands.admin_commands.admin_products import *
from commands.admin_commands.admin_quizes import *
from commands.admin_commands.admin_user_monitoring import *
from commands.dev_tools import *
from config import DEV_KEY
from base.models import *
from commands.bot_utils import button_handler


@button_handler
async def admin_menu_handler(update: Update, context: CallbackContext,
                             admin: User, session: Session, action: str):
    if admin.last_msg_is_photo:
        await context.bot.deleteMessage(chat_id=admin.chat_id,
                                        message_id=admin.last_message_id)
        admin.last_msg_is_photo = False
        message = await context.bot.send_message(chat_id=admin.chat_id,
                                                 text="Перенаправляю..")
        admin.last_message_id = message.message_id
        admin.state = "admin_menu"

    action = action[len("admin_menu::"):]

    action_fields = action.split("_")
    data = action_fields[-1]
    action_command = "_".join(action_fields[:-1])

    if data.isnumeric():
        data = int(data)
        if action_command == "products_block_chosen":
            admin.current_block = data
            data = 0
            action_command = "products_block"
        elif action_command == "questions_block_chosen":
            admin.current_block = data
            data = 0
            action_command = "questions_block"

        await eval(f"{action_command}(update, context, admin, session, data)")

    else:
        if action == "menu":
            admin.admin_current_page = 0
            action = "admin_menu"

        await eval(f"{action}(update, context, admin, session)")

    admin.save(session)


async def admin_distribute_text(update: Update, context: CallbackContext,
                                admin: User, session: Session):
    if admin.state == "products_add":
        await products_add(update, context, admin, session)

    elif admin.state == "product_edit":
        await product_edit_attr(update, context, admin, session)

    elif admin.state == "questions_add":
        await questions_add(update, context, admin, session)

    elif admin.state == "sleeping_notify_confirm":
        await sleeping_notify(update, context, admin, session)

    elif admin.state == "low_results_confirm":
        await low_results_notify(update, context, admin, session)

    elif admin.state == "question_edit":
        await question_edit_attr(update, context, admin, session)

    elif update.message.text == DEV_KEY:
        admin.is_dev = True

    elif admin.is_dev and update.message.text == "/delete_db":
        await delete_db()

    else:
        admin.state = "keyboard"
        await admin_menu(update, context, admin, session)

    admin.save(session)
