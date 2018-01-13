#!/usr/bin/python3

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from marshmallow import Schema, fields
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
 
Base = declarative_base()
 
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

class Terminal(Base):
    __tablename__ = 'terminals'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    key = Column(String(64), nullable=False)

class Functionality(Base):
    __tablename__ = 'functionalities'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)
    terminal_id = Column(Integer, ForeignKey('terminals.id'))
    terminal = relationship(Terminal)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    quantity = Column(Integer)
    minquantity = Column(Integer)
    price = Column(Integer)
    barcode = Column(String(32), nullable=True)
    pictureURL = Column(String(512), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Category)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    balance = Column(Integer)
    type = Column(Integer)

class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    value = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)


class TransactionItem(Base):
    __tablename__ = 'transaction_items'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    quantity = Column(Integer)
    price_per_item = Column(Integer)
    canceled = Column(Boolean, default=False)
    canceled_date = Column(DateTime)
    element_id = Column(Integer, ForeignKey('items.id'))
    element = relationship(Item)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    transaction = relationship(Transaction)
 
class UserSchema(Schema):

    class Meta:
        fields = ("id", "name", "balance")


class ItemSchema(Schema):

    class Meta:
        fields = ("id", "name")


class TransactionItemSchema(Schema):
    element = fields.Nested(ItemSchema)
    class Meta:
        fields = ("id", "date", "value", "element_id", "element")


class TransactionSchema(Schema):
    user = fields.Nested(UserSchema)
    transactionItems = fields.Nested(TransactionItemSchema, many=True)
    class Meta:
        fields = ("id", "date", "value", "user_id", "user", "transactionItems")

#Create Database
engine = create_engine("sqlite:///db.db", echo=True)
Base.metadata.create_all(engine)

