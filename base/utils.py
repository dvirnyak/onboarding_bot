from .models import User, Product


def get_user(update, session):
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


def get_product(block, index, session):
    products = (
        session.query(Product).filter_by(block=block).all())

    print(len(products), index)

    if products is None or len(products) <= index:
        return None

    return products[index]
