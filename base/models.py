import json
from typing import List
import sqlalchemy as db
from sqlalchemy import Integer, Boolean, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from config import Session
from datetime import datetime


class Base(DeclarativeBase):
    pass


class CRUD:
    id = None

    def save(self, session):
        if self.id is None:
            session.add(self)
        return session.commit()

    def destroy(self, session):
        session.delete(self)
        return session.commit()


class User(Base, CRUD):
    __tablename__ = "user_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(60), nullable=True)
    chat_id: Mapped[int] = mapped_column(Integer())

    last_msg_is_photo: Mapped[str] = mapped_column(Boolean(), default=False)
    last_msg_has_keyboard: Mapped[str] = mapped_column(Boolean, default=False)
    last_message_id: Mapped[int] = mapped_column(Integer(), default=0)
    button_number: Mapped[int] = mapped_column(Integer(), default=0)
    state: Mapped[str] = mapped_column(String(30), default="initial")
    current_block: Mapped[int] = mapped_column(Integer(), default=0)
    max_block: Mapped[int] = mapped_column(Integer(), default=0)
    current_product: Mapped[int] = mapped_column(Integer(), default=0)
    current_question: Mapped[int] = mapped_column(Integer(), default=0)
    last_quiz_started: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    quiz_index: Mapped[int] = mapped_column(Integer(), default=0)

    records: Mapped[List["Record"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
    admin_notifications: Mapped[int] = mapped_column(Integer(), default=0b111)
    admin_cache: Mapped[str] = mapped_column(String(10000), nullable=True, default=None)
    admin_current_page: Mapped[int] = mapped_column(Integer(), default=0)

    is_dev: Mapped[bool] = mapped_column(Boolean(), default=False)

    def __repr__(self) -> str:
        return f"{self.chat_id}, {self.first_name} {self.last_name}"

    def tg_str(self) -> str:
        return (f"<a href='tg://openmessage?"
                f"user_id={self.chat_id}'>👤 {self.first_name} "
                f"{self.last_name if not self.last_name is None else ''}</a>")

    def name_str(self) -> str:
        return (f"👤 {self.first_name} "
                f"{self.last_name if not self.last_name is None else ''}")


class Question(Base, CRUD):
    __tablename__ = "question_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(1000))
    block: Mapped[int] = mapped_column(Integer())

    options: Mapped[str] = mapped_column(String(10000), default="null")
    correct_answer: Mapped[int] = mapped_column(Integer())

    records: Mapped[List["Record"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"{self.text}"

    def tg_str(self) -> str:
        question_str = f"❓ {self.text}\n\n"
        # collecting options
        keyboard = []
        options = json.loads(self.options)
        for i in range(len(options)):
            question_str += f"{i + 1}) {options[i]}\n"

        return question_str


class Record(Base, CRUD):
    __tablename__ = "records_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"))
    user: Mapped["User"] = relationship(back_populates="records")

    question_id: Mapped[int] = mapped_column(ForeignKey("question_table.id"))
    question: Mapped["Question"] = relationship(back_populates="records")

    answer: Mapped[int] = mapped_column(Integer())
    is_correct: Mapped[bool] = mapped_column(Boolean())
    submitted: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now)
    block: Mapped[int] = mapped_column(Integer())
    quiz_index: Mapped[int] = mapped_column(Integer())


class Product(Base, CRUD):
    __tablename__ = "product_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))

    price: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    together: Mapped[str] = mapped_column(String(5000))
    effects: Mapped[str] = mapped_column(String(5000))
    image_path: Mapped[str] = mapped_column(String(255))

    block: Mapped[int] = mapped_column(Integer())

    def __repr__(self) -> str:
        return f"📦 {self.title}"

    def tg_str(self):
        text = (f"<b>{self.title}</b>\n\n"
                f"📝 Описание: {self.description}\n\n"
                f"💵 Цена: {self.price}\n\n"
                f"🥂 Совмещают с\n- ")
        text += "\n- ".join(json.loads(self.together))
        text += "\n\n✨ Эффекты:\n- " + "\n- ".join(json.loads(self.effects))

        return text
