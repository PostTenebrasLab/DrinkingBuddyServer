#! /usr/bin/python3
# -*- coding: utf-8 -*-

#
#   Description : Server 
#
#
import json
import datetime
import time
import siphash
import binascii
import os
import sys
import datetime
from flask import Flask, request, jsonify, Response
from flask_restful import Resource, Api
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drinkingBuddyDB_declarative import Base, Category, Inventory, User, Transaction

__author__ = 'Sebastien Chassot'
__author_email__ = 'seba.ptl@sinux.net'

__version__ = "1.0.1"
__copyright__ = ""
__licence__ = "GPL"
__status__ = ""

key = b'0123456789ABCDEF'

engine = create_engine('sqlite:///drinkingBuddy.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


app = Flask(__name__)
api = Api(app)

@app.route("/DrinkingBuddy/sync", methods=['GET'])
def sync():
    """ return drinks catalog


    :return: JSON request tous les capteurs de la classe
    """
    sip = siphash.SipHash_2_4(key)

    now = round(time.time()/60)
    elements = session.query(Inventory, Inventory.name, Inventory.price).filter(Inventory.quantity > 0).all()
    catalog = [e.name + " " + "{:.2f}".format(e.price/100) for e in elements]
    request = {'Header': "DrinkingBuddy", 'Products': catalog, 'Time': now}

    hash_str = request['Header'] + "".join(catalog) + now.__str__()
    for c in hash_str:
        sip.update(binascii.a2b_qp(c))

    request['Hash'] = hex(sip.hash())[2:].upper()
    
    return json.dumps(request)


@app.route("/DrinkingBuddy/buy", methods=['POST'])
def buy():
    """ buy request
    

    :return: JSON request tous les capteurs de la classe
    """
    sipout = siphash.SipHash_2_4(key)
    sipin = siphash.SipHash_2_4(key)

    now = round(time.time()/60)

    dict_req = request.get_json()

    badge = dict_req['Badge']
    product = dict_req['Product']
    time_req = dict_req['Time']

    hash_verif = badge + str(product) + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    if dict_req['Hash'] == hex(sipin.hash())[2:].upper():
        print("Cool hash's OK")
    else:
        print("Pas Cool !!!!!!!!!!")
    print(badge + " " + product + " " + time_req + " " + dict_req['Hash'])

    currentUser = session.query(User).filter(User.id == int(badge,16)).one()
    currentItem = session.query(Inventory).filter(Inventory.id == int(product)).one()

    currentUser.balance = currentUser.balance - currentItem.price
    currentItem.quantity = currentItem.quantity - 1
    ret = []
    if(currentItem.quantity < 0):
        session.rollback()
        print('product not in stock anymore')
        ret = {'Melody': "sad melody", 'Message': ['Product not in stock anymore', 'Please choose something else'], 'Time': now.__str__()}
    elif(currentUser.balance < 0):
        session.rollback()
        print('not enough money in the account!')
        ret = {'Melody': "sad melody", 'Message': ['Not enough money in the account!', 'Get Rich or Die Trying'], 'Time': now.__str__()}
    else:
        session.commit()
        print([currentUser.name, "{:.2f}".format(currentUser.balance/100)])
        new_transaction = Transaction(date = datetime.datetime.now(), value = 1, user = currentUser, element = currentItem)
        session.add(new_transaction)
        ret = {'Melody': "a1b1c1d1e1f1g1", 'Message': ['Successfull transaction', 'Have a nice day'], 'Time': now.__str__()}
    
    hash_str = ret['Melody'] + "".join(ret['Message']) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    ret['Hash'] = hex(sipout.hash())[2:].upper()

    return json.dumps(ret)

@app.route("/DrinkingBuddy/balance", methods=['POST'])
def getBalance():
    """ Get balance request
    

    :return: JSON request tous les capteurs de la classe
    """
    sipout = siphash.SipHash_2_4(key)
    sipin = siphash.SipHash_2_4(key)

    now = round(time.time()/60)

#    if request._headers['Content-Type'] == 'application/json':
    dict_req = request.get_json()

    badge = dict_req['Badge']
    time_req = dict_req['Time']

    hash_verif = badge + time_req
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    if dict_req['Hash'] == hex(sipin.hash())[2:].upper():
        print("Cool hash's OK")
    else:
        print("Pas Cool !!!!!!!!!!")
   
    badgeId = int(badge, 16)
    element = session.query(User, User.name, User.balance).filter(User.id == badgeId)
    if element.count() == 0:
        messages = ['Unknown User', '0.00']
        ret = {'Melody': "c5", 'Message': messages, 'Time': now}
    else:
        messages = [element.one().name, "{:.2f}".format(element.one().balance/100)]
        ret = {'Melody': "a1c1a1c1a1c1a1c1", 'Message': messages, 'Time': now}
    
    
    hash_str = ret['Melody'] + "".join(messages) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    ret['Hash'] = hex(sipout.hash())[2:].upper()

    return json.dumps(ret)

class BeverageList(Resource):
	def get(self):
		beverages = session.query(Inventory).all()
		return {'test':'test'}

class Beverage(Resource):
	def get(self, beverage_id):
		return {'beverage_id':beverage_id}

api.add_resource(BeverageList, '/beverages')
api.add_resource(Beverage, '/beverage/<beverage_id>');

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int('5000')
    )
