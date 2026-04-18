from datetime import datetime  # noqa: TC003 (if typing.TYPE_CHECKING:)

from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    functionalities: Mapped[list[Functionality]] = relationship(back_populates='category')
    items: Mapped[list[Item]] = relationship(back_populates='category')


class Terminal(Base):
    __tablename__ = 'terminals'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    functionalities: Mapped[list[Functionality]] = relationship(back_populates='terminal')


class Functionality(Base):
    __tablename__ = 'functionalities'

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    terminal_id: Mapped[int] = mapped_column(ForeignKey('terminals.id'))
    category: Mapped[Category] = relationship(back_populates='functionalities')
    terminal: Mapped[Terminal] = relationship(back_populates='functionalities')


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer)
    minquantity: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)
    barcode: Mapped[str] = mapped_column(String(32), nullable=True)
    pictureURL: Mapped[str | None] = mapped_column(String(512), nullable=True)  # noqa: N815 (mixedCase)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    category: Mapped[Category] = relationship(back_populates='items')
    transaction_items: Mapped[list[TransactionItem]] = relationship(back_populates='element')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    balance: Mapped[int] = mapped_column(Integer)
    type: Mapped[int] = mapped_column(Integer)
    ldap_user: Mapped[str | None] = mapped_column(String(50))
    cards: Mapped[list[Card]] = relationship(back_populates='user')
    lockers: Mapped[list[Locker]] = relationship(back_populates='user')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='user')


class Card(Base):
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User] = relationship(back_populates='cards')


class Locker(Base):
    __tablename__ = 'locker'

    id: Mapped[int] = mapped_column(primary_key=True)
    lockername: Mapped[str] = mapped_column(String(2))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User] = relationship(back_populates='lockers')


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    value: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User] = relationship(back_populates='transactions')
    items: Mapped[list[TransactionItem]] = relationship(back_populates='transaction')


class TransactionItem(Base):
    __tablename__ = 'transaction_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    quantity: Mapped[int] = mapped_column(Integer)
    price_per_item: Mapped[int] = mapped_column(Integer)
    canceled_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    element_id: Mapped[int] = mapped_column(ForeignKey('items.id'))
    transaction_id: Mapped[int] = mapped_column(ForeignKey('transactions.id'))
    element: Mapped[Item] = relationship(back_populates='transaction_items')
    transaction: Mapped[Transaction] = relationship(back_populates='items')
