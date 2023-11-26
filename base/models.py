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
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(60))
    chat_id: Mapped[int] = mapped_column(Integer())

    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
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

    def __repr__(self) -> str:
        return f"{self.chat_id}, {self.first_name} {self.last_name}"


class Question(Base, CRUD):
    __tablename__ = "question_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(500))
    block: Mapped[int] = mapped_column(Integer())

    option_1: Mapped[str] = mapped_column(String(100))
    option_2: Mapped[str] = mapped_column(String(100), default=None, nullable=True)
    option_3: Mapped[str] = mapped_column(String(100), default=None, nullable=True)
    option_4: Mapped[str] = mapped_column(String(100), default=None, nullable=True)
    option_5: Mapped[str] = mapped_column(String(100), default=None, nullable=True)

    options_count: Mapped[int] = mapped_column(Integer())
    correct_answer: Mapped[int] = mapped_column(Integer())

    records: Mapped[List["Record"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (f"{self.text}\n1) {self.option_1}\n"
                f"2) {self.option_2}\n"
                f"3) {self.option_3}\n"
                f"4) {self.option_4}\n"
                f"5) {self.option_5}\n")


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
    description: Mapped[str] = mapped_column(String(500))
    together: Mapped[str] = mapped_column(String(500))
    effects: Mapped[str] = mapped_column(String(500))
    image_path: Mapped[str] = mapped_column(String(255))

    block: Mapped[int] = mapped_column(Integer())

    def __repr__(self) -> str:
        return (f"{self.title}"
                f"\n\n{self.description}")


