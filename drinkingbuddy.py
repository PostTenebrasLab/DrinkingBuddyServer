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
from flask import Flask, request, jsonify, Response, g
from flask.ext.cors import CORS
from flask_restful import Resource, Api
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, joinedload, lazyload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import func
from drinkingBuddyDB_declarative import Base, Category, Inventory, User, Transaction, TransactionSchema
from collections import OrderedDict
from random import randint
#from flask_simpleldap import LDAP
from pprint import pprint

__author__ = 'Sebastien Chassot'
__author_email__ = 'seba.ptl@sinux.net'

__version__ = "1.0.1"
__copyright__ = ""
__licence__ = "GPL"
__status__ = ""

key = b'0123456789ABCDEF'

engine = create_engine('sqlite:////data/www_app/drinkingbuddy/drinkingBuddy.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


app = Flask(__name__)

app.config['LDAP_BASE_DN'] = 'OU=users,dc=example,dc=org'
app.config['LDAP_USERNAME'] = 'CN=user,OU=Users,DC=example,DC=org'
app.config['LDAP_PASSWORD'] = 'password'

#ldap = LDAP(app)


app.debug = True


CORS(app)

api = Api(app)

@app.route("/sync", methods=['GET'])
def sync():
    """ return drinks catalog


    :return: JSON request tous les capteurs de la classe
    """
    sip = siphash.SipHash_2_4(key)

    now = round(time.time())
    elements = session.query(Inventory, Inventory.name, Inventory.price).filter(Inventory.quantity > 0).all()
    elementsID = session.query(Inventory, Inventory.id).filter(Inventory.quantity > 0).all()

    catalog = [e.name + " " + "{:.2f}".format(e.price/100) for e in elements]
    catalogDBID = [e.id for e in elementsID]
    request = {'Header': "DrinkingBuddy", 'Products': catalog, 'DBID': catalogDBID, 'Time': now}

    hash_str = request['Header'] + "".join(catalog) + now.__str__()
    for c in hash_str:
        sip.update(binascii.a2b_qp(c))

    #reqHash = hex(sip.hash())[2:-1].upper()  #This change is not working on Coltello, but works on the RaspberryPi!!!
    reqHash = hex(sip.hash())[2:].upper()
    reqHash = reqHash.zfill(16)

    request['Hash'] = reqHash

    print(request['Hash'])

    return json.dumps(request)


@app.route("/buy", methods=['POST'])
def buy():
    """ buy request


    :return: JSON request tous les capteurs de la classe
    """
    sipout = siphash.SipHash_2_4(key)
    sipin = siphash.SipHash_2_4(key)

    now = round(time.time())

    dict_req = request.get_json()

    badge = dict_req['Badge']
    product = dict_req['Product']
    time_req = dict_req['Time']
    print("Buying: " + product + " Badge: " + badge)

    hash_verif = badge + str(product) + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    #reqHash = hex(sipin.hash())[2:-1].upper();  #This change not working on coltello, works on raspberry
    reqHash = hex(sipin.hash())[2:].upper();
    reqHash = reqHash.zfill(16)

    if dict_req['Hash'] == reqHash:
        print("Cool hash's OK")
    else:
        print("Hash pas Cool !!!!!!!!!!")
        return json.dumps("ERROR")
    print(badge + " " + product + " " + time_req + " " + dict_req['Hash'])

    currentUser = session.query(User).filter(User.id == int(badge,16)).one()
    currentItem = session.query(Inventory).filter(Inventory.id == int(product)).one()
    currentItem.quantity = currentItem.quantity - 1
    currentUser.balance = currentUser.balance - currentItem.price


    ret = []
    if(currentItem.quantity < 0):
        session.rollback()
        print('product not in stock anymore' + str(currentItem.price) + " " + currentItem.name + "  " + str(currentItem.quantity))
        ret = {'Melody': "b2c3b2", 'Message': ['ERROR', 'Not in stock'], 'Time': now.__str__()}
    elif(currentUser.balance + currentItem.price < currentItem.price):  #we do the + price again because we need to compare before deducting the price
        session.rollback()
        print('not enough money in the account!')
        ret = {'Melody': "b2c3b2", 'Message': ['ERROR', 'Too poor!'], 'Time': now.__str__()}
    else:
        print([currentUser.name, "{:.2f}".format(currentUser.balance/100)])
        new_transaction = Transaction(date = datetime.datetime.now(), value = 1, user = currentUser, element = currentItem)
        session.add(new_transaction)
        ret = {'Melody': "a1b1c1d1e1f1g1", 'Message': ['Successfull transaction', 'Have a nice day'], 'Time': now.__str__()}
        #if(randint(1,20) != 20 & currentItem.category_id == 2) #If 20 (5% chance) then we give a free beer!  ----> Syntax needs to be corrected
        #    currentUser.balance = currentUser.balance + currentItem.price #Give back the money
        #    ret = {'Melody': "2d2a1f2c2d2a2d2c2f2d2a2c2d2a1f2c2d2a2a2g2p8p8p8p", 'Message': ['YOU WON!!! :)', 'FREE BEER!'], 'Time': now.__str__()}
        session.commit()

    hash_str = ret['Melody'] + "".join(ret['Message']) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    #retHash = hex(sipout.hash())[2:-1].upper()  #This change not working on Coltello, works on Raspbbery
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    ret['Hash'] = retHash

    return json.dumps(ret)

@app.route("/balance", methods=['POST'])
def getBalance():
    """ Get balance request


    :return: JSON request tous les capteurs de la classe
    """
    sipout = siphash.SipHash_2_4(key)
    sipin = siphash.SipHash_2_4(key)

    now = round(time.time())

#    if request._headers['Content-Type'] == 'application/json':
    dict_req = request.get_json()

    badge = dict_req['Badge']
    time_req = dict_req['Time']

    hash_verif = badge + time_req
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    #reqHash = hex(sipin.hash())[2:-1].upper() #This change does not work on Coltello
    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)

    if dict_req['Hash'] == reqHash:
        print("Cool hash's OK")
    else:
        print("Pas Cool !!!!!!!!!!")

    badgeId = int(badge, 16)
    element = session.query(User, User.name, User.balance).filter(User.id == badgeId)
    if element.count() == 0:
        messages = ['ERROR', 'UNKNOWN USER']
        ret = {'Melody': "c5", 'Message': messages, 'Time': now}
    else:
        messages = [element.one().name, "{:.2f}".format(element.one().balance/100)]
        ret = {'Melody': "a1c1a1c1a1c1a1c1", 'Message': messages, 'Time': now}


    hash_str = ret['Melody'] + "".join(messages) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    #retHash = hex(sipout.hash())[2:-1].upper()  #This change does not work on Coltello works on PI
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    ret['Hash'] = retHash

    return json.dumps(ret)

@app.route("/total", methods=['GET'])
def total():

    date_from = request.args['from']
    date_to = request.args['to']

    query = session.query(
        #func.month(Transaction.date).label("period"),  #sql only
        func.sum(Transaction.value).label("transaction_value"),
        func.count(Transaction.id).label("transaction_count"),
    ).filter(Transaction.date.between(date_from, date_to))

    #query.group_by(func.month(Transaction.date)) #sql only

    results = [str(e.transaction_value) + " " + str(e.transaction_count) for e in query.all()]

    return json.dumps(results)

@app.route("/beverages", methods=['GET'])
def getBeverages():
    beverages =  [
        serialize(beverage)
        for beverage in session.query(Inventory).all()
    ]
    return json.dumps(beverages)

@app.route("/beverages", methods=['POST'])
def postBeverages():
    data = request.get_json(force=True)
    pprint(json)
    beverage = Inventory(name = data['name'], quantity = data['quantity'])
    session.add(beverage)
    session.commit()
    return json.dumps(serialize(beverage))

#class BeverageListResource(Resource):
#
#       def get(self):
#               beverages =  [
#                       serialize(beverage)
#                       for beverage in session.query(Inventory).all()
#               ]
#               return beverages
#
#       def post(self):
#               beverage = Inventory(name = request.json['name'], quantity = request.json['quantity'])
#               session.add(beverage)
#               session.commit()
#               return serialize(beverage)



class BeverageResource(Resource):
        def get(self, beverage_id):
                beverage = serialize(session.query(Inventory).filter(Inventory.id == beverage_id).one())
                return beverage

        def post(self, beverage_id):
                beverage = session.query(Inventory).filter(Inventory.id == beverage_id).first()
                for (field, value) in request.json.items():
                        setattr(beverage,field,value)

                session.commit()
                return serialize(beverage)

class UserListResource(Resource):
        def get(self):
                #users = session.query(User, User.id, User.name, User.balance).all()

                users = [
                        serialize(user)
                        for user in session.query(User).all()
                ]
                return users


class UserResource(Resource):
        def get(self, user_id):
                user = serialize(session.query(User).filter(User.id == user_id).one())
                return serialize(user)

class TransactionListResource(Resource):
        def get(self):
                transactions = session.query(Transaction).options(lazyload('*')).all()
                result, error = TransactionSchema(many=True).dump(transactions)
                #print(transactions[0].element.name)
                return result


def serialize(model):
        columns = [c.key for c in class_mapper(model.__class__).columns]
        return dict((c, getattr(model, c)) for c in columns)

#api.add_resource(BeverageListResource, '/beverages')

api.add_resource(BeverageResource, '/beverages/<beverage_id>')

api.add_resource(UserListResource, '/users')
api.add_resource(UserResource, '/users/<user_id>')

api.add_resource(TransactionListResource, '/transactions')

if __name__ == "__main__":
    app.run(host="0.0.0.0")
