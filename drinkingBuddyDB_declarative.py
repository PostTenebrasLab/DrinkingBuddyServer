import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()
 
class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    quantity = Column(Integer)
    price = Column(Integer)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    balance = Column(Integer)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    value = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)
    element_id = Column(Integer, ForeignKey('inventory.id'))
    element = relationship(Inventory)
 
#Create Database
#engine = create_engine("sqlite:///db.db", echo=True)
#Base.metadata.create_all(engine)

