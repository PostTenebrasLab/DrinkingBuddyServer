#! /usr/bin/python3
# -*- coding: utf-8 -*-

#
#   Description : Server
#
#
import base64
import json
import datetime
import time
import siphash
import binascii
import os
import sys
from http import HTTPStatus
from decimal import Decimal
#from datetime import timedelta
import flask
from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS
from flask_restful import Resource, Api
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship, joinedload, lazyload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, exc, class_mapper
from sqlalchemy.sql import func
# from .drinkingBuddyDB_declarative import Base, Category, Inventory, User, Transaction, TransactionSchema
from .drinkingBuddyDB_declarative import Base, Category, Item, Terminal, Card, User, Transaction, TransactionItem, Functionality, Locker
from collections import OrderedDict
from random import randint
#import paho.mqtt.client as paho
#from flask_simpleldap import LDAP
from pprint import pprint

try:
    # check for local configuration
    # defines variables to not push on github
    import localconfig
    dbpath = localconfig.dbpath
    dbuser = localconfig.dbuser
    dbpasswd = localconfig.dbpasswd
except:
    # use default development test values
    # dev path to DB in same dir as script
    dbpath = 'sqlite:////data/drinkingBuddy.db'
    dbuser = "ptllocker1"
    dbpasswd = "P0stL0ck"


__author__ = 'Sebastien Chassot'
__author_email__ = 'seba.ptl@sinux.net'

__version__ = "1.0.1"
__copyright__ = ""
__licence__ = "GPL"
__status__ = ""


engine = create_engine(dbpath)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


app = Flask(__name__)

app.config['LDAP_BASE_DN'] = 'OU=users,dc=example,dc=org'
app.config['LDAP_USERNAME'] = 'CN=user,OU=Users,DC=example,DC=org'
app.config['LDAP_PASSWORD'] = 'password'
broker = "mqtt.lan.posttenebraslab.ch"

# create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection$
#client = paho.Client("client-001")
#client.username_pw_set(dbuser, dbpasswd)
#print("publishing ")
# client.disconnect() #disconnect


#ldap = LDAP(app)


#app.debug = True
#DEVEL_TEST = True


CORS(app)

api = Api(app)


def basic_auth():
    authorization = flask.request.authorization
    if authorization is None:
        flask.abort(HTTPStatus.UNAUTHORIZED, "auth-none")

    if authorization.type != "basic":
        flask.abort(HTTPStatus.UNAUTHORIZED, f"auth-type: {authorization.type}")

    username = authorization.username
    password = authorization.password
    terminal = session.query(Terminal, Terminal.id).filter(
        Terminal.name == username,
        Terminal.key == password,
    ).one_or_none()
    if terminal is None:
        flask.abort(HTTPStatus.UNAUTHORIZED, f"auth-credentials: {username}:{password}")

    return terminal

def base64url_decode(b64: str):
    b64 += '=' * (4 - len(b64) % 4)
    return base64.urlsafe_b64decode(b64)
def ceil_div(n, d):
    return -(n // -d)
def int_to_base64url(i: int):
    bytes_count = ceil_div(i.bit_length(), 8)
    bs = i.to_bytes(bytes_count)
    return base64.urlsafe_b64encode(bs).rstrip(b'=').decode('ascii')

@app.route("/badge/<id>", methods=["GET"])
def badge(id: str):
    terminal = basic_auth()

    badge_id_bytes = base64url_decode(id)
    card_id = int.from_bytes(badge_id_bytes)

    user = session.query(User, User.id, User.name, User.balance).join(Card, User.id == Card.user_id).filter(Card.id == card_id).one_or_none()
    if user is None:
        flask.abort(HTTPStatus.NOT_FOUND, f"card.id {card_id}")

    return dict(
        id=int_to_base64url(user.id),
        name=user.name,
        balance=user.balance,
    )

@app.route("/barcode/<data>", methods=["GET"])
def barcode(data: str):
    terminal = basic_auth()

    data_bytes = base64url_decode(data)
    item_barcode = data_bytes.decode('ascii')

    item = session.query(Item, Item.id, Item.name, Item.price).filter(Item.barcode == item_barcode).one_or_none()
    if item is None:
        flask.abort(HTTPStatus.NOT_FOUND, f"item.barcode {item_barcode}")

    return dict(
        id=int_to_base64url(item.id),
        name=item.name,
        cost=item.price,
    )


@app.route("/sync", methods=['POST'])
def sync():
    """ return drinks catalog based on terminal id

    curl -X POST -H 'Content-Type: application/json' -d '{"Tid":"1"}' http://localhost:5000/sync

    :return: JSON request toutes les categories accessible a un terminal
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
    except KeyError:
        return json.dumps({"DrinkingBuddy sync error": "Unknown terminal ID or key"})

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    query_elementsID = session.query(Item, Functionality, Item.id, Item.name,
                                     Item.price).filter(Functionality.terminal_id == termid,
                                                        Item.quantity > 0, Functionality.category_id == Item.category_id)

    catalog = [[e.id, e.name, "{:.2f}".format(
        e.price/100)] for e in query_elementsID]

    response = {'Header': "DrinkingBuddy", 'Products': catalog, 'Time': now}

    hash_str = response['Header']
    for e in query_elementsID:
        hash_str += str(e.id)
        hash_str += e.name
        hash_str += "{:.2f}".format(e.price/100)
    hash_str += now.__str__()

    for c in hash_str:
        sipin.update(binascii.a2b_qp(c))

    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)

    response['Hash'] = reqHash

    if app.debug:
        print(hash_str)
        print(response['Hash'])

    return json.dumps(response)

@app.route("/gettime", methods=['POST'])
def gettime():
    """ return drinks catalog based on terminal id

    curl -X POST -H 'Content-Type: application/json' -d '{"Tid":"1"}' http://localhost:5000/time

    :return: JSON request toutes les categories accessible a un terminal
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
    except KeyError:
        return json.dumps({"DrinkingBuddy sync error": "Unknown terminal ID or key"})

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    response = {'Header': "DrinkingBuddy", 'Melody': 'c1', 'Time': now}

    hash_str = response['Header']
    hash_str += now.__str__()

    for c in hash_str:
        sipin.update(binascii.a2b_qp(c))

    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)

    response['Hash'] = reqHash

    if app.debug:
        print(hash_str)
        print(response['Hash'])

    return json.dumps(response)



@app.route("/user", methods=['POST'])
def getUser():
    """ Get user request


    :return: JSON 
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        sent_hash = dict_req['Hash']
    except KeyError:
        return json.dumps({"DrinkingBuddy user error": "Unknown key(s)"})

    try:
        time_req = dict_req['Time']
    except KeyError:
        time_req = 0

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()

    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    hash_verif = badge + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    # reqHash = hex(sipin.hash())[2:-1].upper() #This change does not work on Coltello
    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)
    badgeId = int(badge, 16)

    if dict_req['Hash'] == reqHash:
        print("Cool hash's OK")
        print("Get user badge: " + str(badgeId))
    else:
        print("Pas Cool !!!!!!!!!!")

    element = session.query(User, User.name).join(Card).filter(
        User.id == Card.user_id, Card.id == badgeId, User.type == 1)
    if element.count() == 0:
        messages = ['ERROR', 'UNKNOWN USER']
        ret = {'Melody': "c5", 'Message': messages, 'Time': now}
    else:
        # TEMP the 100/100 should be replaced by group ID or other info
        messages = [element.one().name, "{:.2f}".format(100/100)]
        ret = {'Melody': "a1c1a1c1a1c1a1c1", 'Message': messages, 'Time': now}

    hash_str = ret['Melody'] + element.one().name + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    # retHash = hex(sipout.hash())[2:-1].upper()  #This change does not work on Coltello works on PI
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    ret['Hash'] = retHash

    return json.dumps(ret)


@app.route("/add", methods=['POST'])
def add():
    """ add request



    :return: JSON 
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        product = dict_req.get('Product')
        barcode = dict_req.get('Barcode')
        item_count = dict_req.get('Item_count')
        item_category = dict_req.get('Item_category')
        time_req = dict_req['Time']
        sent_hash = dict_req['Hash']
    except KeyError:
        return json.dumps({"DrinkingBuddy add error": "Unknown key(s)"})
    if not product and not barcode:
        return json.dumps({"ERROR": "Missing barcode or product ID"})

    if not item_count:
        item_count = 1

    if not product:
        useBarcode = True
    else:
        useBarcode = False

    print(dict_req)

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()

    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    if app.debug:
        if useBarcode:
            print("Adding: " + barcode + " Badge: " + badge)
        else:
            print("Adding: " + product + " Badge: " + badge)

    if useBarcode:
        hash_verif = badge + str(barcode) + str(time_req)
    else:
        hash_verif = badge + str(product) + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    req_hash = hex(sipin.hash())[2:].upper()
    req_hash = req_hash.zfill(16)

    if sent_hash == req_hash:
        if app.debug and DEVEL_TEST:
            print("Cool hash's OK and is "+str(req_hash))
    else:
        if app.debug:
            print("Hash pas Cool !!!!!!!!!!")
        return json.dumps({"DrinkingBuddy error": "Hash error "+str(req_hash)})

    if app.debug:
        if useBarcode:
            print(badge + " " + barcode + " " +
                  time_req + " " + dict_req['Hash'])
        else:
            print(badge + " " + product + " " +
                  time_req + " " + dict_req['Hash'])

    try:
        currentUser = session.query(User).join(Card).filter(
            Card.user_id == User.id, Card.id == int(badge, 16)).one()
        if useBarcode:
            currentItem = session.query(Item).filter(
                Item.barcode == barcode.rstrip("\r\n")).one()
        else:
            currentItem = session.query(Item).filter(
                Item.id == int(product)).one()
    except exc.NoResultFound:
        print("SQL Error in add")
        return json.dumps({"ERROR": "Item/barcode does not exist"})

    currentItem.quantity = currentItem.quantity + int(item_count)

    response = []

    # TODO check currentUser to know if he can add items
    if(currentUser.type != 1):
        session.rollback()
        print('User cannot add tems' + str(currentItem.price) + " " +
              currentItem.name + "  " + str(currentItem.quantity))
        response = {'Melody': "b2c3b2", 'Message': [
            'ERROR', 'User cannot add items'], 'Time': now.__str__()}
    else:
        print([currentUser.name, "{:.2f}".format(currentUser.balance/100)])
        # new_transaction = Transaction(date = datetime.datetime.now(), value = 1, user = currentUser, element = currentItem)
        new_transaction = Transaction(
            date=datetime.datetime.now(), value=1, user=currentUser)
        new_transactionitem = TransactionItem(date=datetime.datetime.now(),
                                              quantity=-int(item_count),
                                              price_per_item=currentItem.price,
                                              canceled_date=None,
                                              element_id=currentItem.id,
                                              transaction=new_transaction)
        session.add(new_transaction)
        session.add(new_transactionitem)
        response = {'Melody': "a1a1a1b1b1f1g1", 'Message': [
            'Successfull transaction', 'Have a nice day'], 'Time': now.__str__()}
        session.commit()
        print(response)
    hash_str = response['Melody'] + \
        "".join(response['Message']) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    # retHash = hex(sipout.hash())[2:-1].upper()  #This change not working on Coltello, works on Raspbbery
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    response['Hash'] = retHash

    return json.dumps(response)


@app.route("/buy", methods=['POST'])
def buy():
    """ buy request

    curl -X POST -H 'Content-Type: application/json' -d '{"Tid":"1","Badge":"4285702E","Product":"5","Time":"53677","Hash":"4527E4199D78DC12"}' http://localhost:5000/buy


    :return: JSON request tous les capteurs de la classe
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        product = dict_req.get('Product')
        barcode = dict_req.get('Barcode')
        time_req = dict_req['Time']
        sent_hash = dict_req['Hash']
    except KeyError:
        return json.dumps({"DrinkingBuddy buy error": "Unknown key(s)"})

    if not product and not barcode:
        return json.dumps({"DrinkingBuddy buy error": "Missing barcode or product ID"})

    if not product:
        useBarcode = True
    else:
        useBarcode = False

    print(dict_req)

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()

    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    if app.debug:
        if useBarcode:
            print("Buying: " + barcode + " Badge: " + badge)
        else:
            print("Buying: " + product + " Badge: " + badge)

    if useBarcode:
        hash_verif = badge + str(barcode) + str(time_req)
    else:
        hash_verif = badge + str(product) + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    req_hash = hex(sipin.hash())[2:].upper()
    req_hash = req_hash.zfill(16)

    if sent_hash == req_hash:
        if app.debug and DEVEL_TEST:
            print("Cool hash's OK and is "+str(req_hash))
    else:
        if app.debug:
            print("Hash pas Cool !!!!!!!!!!" + str(req_hash))
        #return json.dumps({"DrinkingBuddy error": "Hash error "+str(req_hash) + "  " + str(sent_hash)})

    if app.debug:
        if useBarcode:
            print(badge + " " + barcode + " " +
                  time_req + " " + dict_req['Hash'])
        else:
            print(badge + " " + product + " " +
                  time_req + " " + dict_req['Hash'])

    try:
        currentUser = session.query(User).join(Card).filter(
            Card.user_id == User.id, Card.id == int(badge, 16)).one()
        if useBarcode:
            currentItem = session.query(Item).filter(
                Item.barcode == barcode.strip()).one()
        else:
            currentItem = session.query(Item).filter(
                Item.id == int(product)).one()
    except exc.NoResultFound:
        print("SQL Error in buy")
        return json.dumps({"DrinkingBuddy buy sql error": "No result found"})

    currentItem.quantity = currentItem.quantity - 1
    currentUser.balance = currentUser.balance - currentItem.price

    response = []
    if(currentItem.quantity < 0 and not useBarcode):
        session.rollback()
        print('product not in stock anymore' + str(currentItem.price) +
              " " + currentItem.name + "  " + str(currentItem.quantity))
        response = {'Melody': "b2c3b2", 'Message': [
            'ERROR', 'Not in stock'], 'Time': now.__str__()}
    # we do the + price again because we need to compare before deducting the price
    elif(currentUser.balance + currentItem.price < currentItem.price):
        session.rollback()
        print('not enough money in the account!')
        response = {'Melody': "b2c3b2", 'Message': [
            'ERROR', 'Too poor!'], 'Time': now.__str__()}
    else:
        print([currentUser.name, "{:.2f}".format(currentUser.balance/100)])
        # new_transaction = Transaction(date = datetime.datetime.now(), value = 1, user = currentUser, element = currentItem)
        new_transaction = Transaction(
            date=datetime.datetime.now(), value=1, user=currentUser)
        new_transactionitem = TransactionItem(date=datetime.datetime.now(),
                                              quantity=1,
                                              price_per_item=currentItem.price,
                                              canceled_date=None,
                                              element_id=currentItem.id,
                                              transaction=new_transaction)
        session.add(new_transaction)
        session.add(new_transactionitem)
        response = {'Melody': "a1b1c1d1e1f1g1", 'Message': [
            'Successfull transaction', currentItem.name], 'Time': now.__str__(), 'ItemPrice':currentItem.price}
        # if(randint(1,20) != 20 & currentItem.category_id == 2) #If 20 (5% chance) then we give a free beer!  ----> Syntax needs to be corrected
        #    currentUser.balance = currentUser.balance + currentItem.price #Give back the money
        #    ret = {'Melody': "2d2a1f2c2d2a2d2c2f2d2a2c2d2a1f2c2d2a2a2g2p8p8p8p", 'Message': ['YOU WON!!! :)', 'FREE BEER!'], 'Time': now.__str__()}
        session.commit()
        print(response)
    hash_str = response['Melody'] + \
        "".join(response['Message']) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    # retHash = hex(sipout.hash())[2:-1].upper()  #This change not working on Coltello, works on Raspbbery
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    response['Hash'] = retHash
#    if currentItem.category_id == 1 or currentItem.category_id == 2:
#        print("Opening fridge by MQTT")
#        client.connect(broker)  # connect
#        client.publish("Fridge", "5")  # publish
#        client.disconnect()

    return json.dumps(response)


@app.route("/balance", methods=['POST'])
def getBalance():
    """ Get balance request
    """
    dict_req = request.get_json()
    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        time_req = dict_req['Time']

    except KeyError:
        return json.dumps({"DrinkingBuddy sync error": "Unknown terminal ID or key"})

    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

#    if request._headers['Content-Type'] == 'application/json':

    hash_verif = badge + time_req
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    # reqHash = hex(sipin.hash())[2:-1].upper() #This change does not work on Coltello
    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)
    badgeId = int(badge, 16)

    if dict_req['Hash'] == reqHash:
        print("Cool hash's OK")
        print("Get user badge: " + str(badgeId))
    else:
        print("Pas Cool !!!!!!!!!!")

    element = session.query(User, User.name, User.balance).join(
        Card).filter(User.id == Card.user_id, Card.id == badgeId)
    if element.count() == 0:
        messages = ['ERROR', 'UNKNOWN USER']
        ret = {'Melody': "c5", 'Message': messages, 'Time': now}
    else:
        messages = [element.one().name, "{:.2f}".format(
            element.one().balance/100)]
        ret = {'Melody': "a1c1a1c1a1c1a1c1", 'Message': messages, 'Time': now}
#        if termid == "4":  # we only want to open if the terminal is a barcode terminal, and only if it is sucessful
#            print("Opening fridge by MQTT")
#            client.connect(broker)  # connect
#            client.publish("Fridge", "9")  # publish
#            client.disconnect()

    hash_str = ret['Melody'] + "".join(messages) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    # retHash = hex(sipout.hash())[2:-1].upper()  #This change does not work on Coltello works on PI
    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    ret['Hash'] = retHash
    print(json.dumps(ret))
    return json.dumps(ret)


@app.route("/total", methods=['GET'])
def total():

    date_from = request.args['from']
    date_to = request.args['to']

    query = session.query(
        # func.month(Transaction.date).label("period"),  #sql only
        func.sum(Transaction.value).label("transaction_value"),
        func.count(Transaction.id).label("transaction_count"),
    ).filter(Transaction.date.between(date_from, date_to))

    # query.group_by(func.month(Transaction.date)) #sql only

    results = [str(e.transaction_value) + " " + str(e.transaction_count)
               for e in query.all()]

    return json.dumps(results)


@app.route("/locker", methods=['POST'])
def getLocker():
    """
    Get locker IDs that can be opened by userID matching sent cardID.
    """
    dict_req = request.get_json()
    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        time_req = dict_req['Time']

    except KeyError:
        return json.dumps({"DrinkingBuddy sync error": "Unknown terminal ID or key"})

    # create hashes
    query_key = session.query(Terminal, Terminal.key).filter(
        Terminal.id == termid).one()
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))

    now = round(time.time())

    # compute hash for checking
    hash_verif = badge + time_req
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    reqHash = hex(sipin.hash())[2:].upper()
    reqHash = reqHash.zfill(16)
    badgeId = int(badge, 16)

    # check input hash.
    hash_ok = False
    if dict_req['Hash'] == reqHash:
        print("Cool hash's OK")
        print("Get user badge: " + str(badgeId))
        hash_ok = True
    else:
        print("Pas Cool !!!!!!!!!!")
        messages = ['ERROR', 'HASH DOES NOT MATCH']
        ret = {'Melody': "c5", 'Message': messages, 'Time': now}

    if hash_ok:
        # get Locker matching user for requested badge ID
        element = session.query(Locker, Locker.lockername).join(User).join(Card).filter(
            User.id == Card.user_id, Card.id == badgeId, Locker.user_id == User.id)
        if element.count() == 0:
            messages = ['ERROR', 'UNKNOWN USER, CARD OR LOCKER']
            ret = {'Melody': "c5", 'Message': messages, 'Time': now}
        else:
            messages = ["{}".format(x.lockername) for x in element]
            ret = {'Melody': "a1a1a1c1c1c1a1c1",
                   'Message': messages, 'Time': now}

    # Prepare output hash
    hash_str = ret['Melody'] + "".join(messages) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    ret['Hash'] = retHash

    # return output
    print(json.dumps(ret))
    return json.dumps(ret)


@app.route("/foodcount", methods=['GET'])
def getFood():
    now = round(time.time())
    foodCount = session.query(TransactionItem, TransactionItem.id).filter(
        TransactionItem.element_id == 5, TransactionItem.date >= datetime.date.today(), TransactionItem.canceled == False).count()
    response = {'Message': ['Food bought today', foodCount],
                'Melody': 'a2', 'Time': now, 'Hash': 'Bidon'}
    print(response)
    print(datetime.date.today())
    return json.dumps(response)


@app.route("/beverages", methods=['GET'])
def getBeverages():
    beverages = [
        serialize(beverage)
        for beverage in session.query(Item).all()
    ]
    return json.dumps(beverages)


@app.route("/beverages/<barcode>", methods=['GET'])
def getBeverageBarcode(barcode):
    try:
        beverage = session.query(Item).filter(Item.barcode == barcode).one()
        return json.dumps(serialize(beverage))
    except exc.NoResultFound:
        return json.dumps(None)


@app.route("/beverages", methods=['POST'])
def postBeverages():
    data = request.get_json(force=True)
    pprint(json)
    beverage = Item(name=data['name'], quantity=data['quantity'])
    session.add(beverage)
    session.commit()
    return json.dumps(serialize(beverage))

@app.route("/addcents", methods=['POST'])
def addcents():
    """ addcents request

    curl -X POST -H 'Content-Type: application/json' -d '{"Tid":"1","Badge":"4285702E","Cents":"5","Time":"53677","Hash":"4527E4199D78DC12"}' http://localhost:5000/addcents


    :return: JSON request tous les capteurs de la classe
    """
    dict_req = request.get_json()

    try:
        termid = dict_req['Tid']
        badge = dict_req['Badge']
        cents = dict_req.get('Cents')
        time_req = dict_req['Time']
        sent_hash = dict_req['Hash']
    except KeyError:
        return json.dumps({"DrinkingBuddy addcents error": "Unknown key(s)"})

    if not cents or not badge:
        return json.dumps({"DrinkingBuddy addcents error": "Missing cents or badge id"})

    if int(cents) < 0:
        return json.dumps({"DrinkingBuddy addcents error": "cents cannot be negative"})

    print(dict_req)

    query_key = session.query(Terminal, Terminal.key).filter(Terminal.id == termid).one()

    sipout = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    sipin = siphash.SipHash_2_4(bytearray(str(query_key.key).encode("utf-8")))
    now = round(time.time())

    if app.debug:
        print("Adding cents: " + str(cents) + " Badge: " + badge)

    hash_verif = badge + str(cents) + str(time_req)
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    req_hash = hex(sipin.hash())[2:].upper()
    req_hash = req_hash.zfill(16)

    if sent_hash == req_hash:
        if app.debug and DEVEL_TEST:
            print("Cool hash's OK and is "+str(req_hash))
    else:
        if app.debug:
            print("Hash pas Cool !!!!!!!!!!" + str(req_hash))
        return json.dumps({"DrinkingBuddy error": "Hash error "+str(req_hash) + "  " + str(sent_hash)})

    if app.debug:
        print(badge + " " + str(cents) + " " + time_req + " " + dict_req['Hash'])

    try:
        currentUser = session.query(User).join(Card).filter(
            Card.user_id == User.id, Card.id == int(badge, 16)).one()
    except exc.NoResultFound:
        print("SQL Error in addcents getting user")
        return json.dumps({"DrinkingBuddy addcents sql error": "No result found"})

    currentUser.balance = currentUser.balance + int(cents)

    response = []
    print([currentUser.name, "{:.2f}".format(currentUser.balance/100)])

    new_transaction = Transaction(
        date=datetime.datetime.now(), value=1, user=currentUser)
    new_transactionitem = TransactionItem(date=datetime.datetime.now(),
                                          quantity=int(cents),
                                          price_per_item=-1,
                                          canceled_date=None,
                                          element_id=1000,
                                          transaction=new_transaction)
    session.add(new_transaction)
    session.add(new_transactionitem)
    response = {'Melody': "a1b1c1d1e1f1g1", 'Message': ['Successfull add cents', str(cents)], 'Time': now.__str__()}
    session.commit()
    print(response)
    hash_str = response['Melody'] + \
        "".join(response['Message']) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    retHash = hex(sipout.hash())[2:].upper()
    retHash = retHash.zfill(16)

    response['Hash'] = retHash
    return json.dumps(response)


# class BeverageListResource(Resource):
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
        beverage = serialize(session.query(Item).filter(Item.id == beverage_id).one())
        return beverage

    def post(self, beverage_id):
        beverage = session.query(Item).filter(Item.id == beverage_id).first()
        for (field, value) in request.json.items():
            setattr(beverage, field, value)

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
        return user


class TransactionListResource(Resource):
    def get(self):
        transactions = session.query(Transaction).options(lazyload('*')).all()
        result, error = TransactionSchema(many=True).dump(transactions)
        # print(transactions[0].element.name)
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
