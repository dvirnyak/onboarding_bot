from typing import List
import sqlalchemy as db
from sqlalchemy import Integer, Boolean, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from config import Session
from datetime import datetime


class Base(DeclarativeBase):
    pass


class CRUD():
    def save(self, session):
        if self.id == None:
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
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
    chat_id: Mapped[int] = mapped_column(Integer())
    button_number: Mapped[int] = mapped_column(Integer(), default=0)
    state: Mapped[str] = mapped_column(String(30), default="initial")
    current_block: Mapped[int] = mapped_column(Integer(), default=0)
    current_product: Mapped[int] = mapped_column(Integer(), default=0)
    current_question: Mapped[int] = mapped_column(Integer(), default=0)

    records: Mapped[List["Record"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"{self.chat_id}, {self.first_name} {self.last_name}"


class Question(Base, CRUD):
    __tablename__ = "question_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(500))

    option_1: Mapped[str] = mapped_column(String(100))
    option_2: Mapped[str] = mapped_column(String(100))
    option_3: Mapped[str] = mapped_column(String(100))
    option_4: Mapped[str] = mapped_column(String(100))
    option_5: Mapped[str] = mapped_column(String(100))

    options_count: Mapped[int] = mapped_column(Integer())
    correct_answer: Mapped[int] = mapped_column(Integer())

    records: Mapped[List["Record"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (f"{self.text}\n1) {self.option_1}\n"
                f"2) {self.option_2}"
                f"3) {self.option_3}"
                f"4) {self.option_4}")


class Record(Base, CRUD):
    __tablename__ = "records_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"))
    user: Mapped["User"] = relationship(back_populates="records")

    question_id: Mapped[int] = mapped_column(ForeignKey("question_table.id"))
    question: Mapped["Question"] = relationship(back_populates="records")

    answer: Mapped[int] = mapped_column(Integer())
    is_correct: Mapped[bool] = mapped_column(Boolean())
    submitted: Mapped[datetime] = mapped_column(TIMESTAMP, default=db.func.now)


class Product(Base, CRUD):
    __tablename__ = "product_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    block: Mapped[int] = mapped_column(Integer())
    description: Mapped[str] = mapped_column(String(500))
    together: Mapped[str] = mapped_column(String(500))
    effects: Mapped[str] = mapped_column(String(500))
    price: Mapped[str] = mapped_column(String(100))
    image_path: Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return (f"{self.title}"
                f"\n\n{self.description}")


