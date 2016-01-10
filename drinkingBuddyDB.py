import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from drinkingBuddyDB_declarative import Base, Category, Inventory, User, Transaction
 
# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///drinkingBuddy.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
#Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

#new_user = User(name='achraf', balance=2000)
#session.add(new_user)

#new_inventory = Inventory(name = 'Bud', quantity = 25, price = 200, category = session.query(Category).filter(Category.name == 'Beer').one());
#session.add(new_inventory)
mydate = datetime.datetime.now();
#new_transaction = Transaction(date = mydate, value = 1, user = session.query(User).filter(User.id == 42).one(), element = session.query(Inventory).filter(Inventory.id == 1).one())
#session.add(new_transaction)

#session.commit()

elements = session.query(Inventory, Inventory.name, Inventory.price).all()

for e in elements:
    print(e.name, e.price/100)




