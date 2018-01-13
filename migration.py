from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload, lazyload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import func
from sqlalchemy import and_
import os
import datetime
import time
import drinkingBuddyDB_declarative as newDB
import drinkingBuddyDB_declarative_old as oldDB

__author__ = 'Michael Jaussi'
__author_email__ = 'michael.jaussi@gmail.com'

__version__ = "0.0.1"
__copyright__ = ""
__licence__ = "GPL"
__status__ = ""


engineOld = create_engine('sqlite:///./drinkingBuddy.db')
engineNew = create_engine('sqlite:///./db.db')

newDB.Base.metadata.drop_all(engineNew)
newDB.Base.metadata.create_all(engineNew)

DBSessionOld = sessionmaker(bind=engineOld)
DBSessionNew = sessionmaker(bind=engineNew)

sessionOld = DBSessionOld()
sessionNew = DBSessionNew()

# migrate users
users = sessionOld.query(oldDB.User);
for u in users:
    new_user = newDB.User(name = u.name, balance = u.balance)
    sessionNew.add(new_user)
    new_card = newDB.Card(id = u.id, user = new_user)
    sessionNew.add(new_card)
sessionNew.commit()
print("migrated Users\n")

# migrate categories
categories = sessionOld.query(oldDB.Category)
for c in categories:
    new_category = newDB.Category(id = c.id, name = c.name)
    sessionNew.add(new_category)
sessionNew.commit()
print("migrated Categories\n")

#migrate inventory
inventory = sessionOld.query(oldDB.Inventory)
for i in inventory:
    new_item = newDB.Item(id = i.id, name = i.name, quantity = i.quantity,
                          minquantity = i.minquantity, price = i.price,
                        barcode = None, pictureURL = None, category_id = i.category_id)
    sessionNew.add(new_item)
sessionNew.commit()
print("migrated Inventory\n")

transactions = sessionOld.query(oldDB.Transaction).join(oldDB.Transaction.element)
for t in transactions:
    new_transaction = newDB.Transaction(id = t.id, date = t.date, value = t.value, user_id = t.user_id);
    sessionNew.add(new_transaction)
    new_transaction_item = newDB.TransactionItem(date = t.date, quantity = t.value,
                                                 price_per_item = t.element.price,
                                                 canceled_date = None, element_id = t.element_id,
                                                 transaction = new_transaction)
    sessionNew.add(new_transaction_item)
sessionNew.commit()
print("migrated Transactions\n")



