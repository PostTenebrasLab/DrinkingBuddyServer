#! /usr/bin/python3
# -*- coding: utf-8 -*-

#
#   Description : Server 
#
#
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
from flask import Flask, request, jsonify, Response
#from flask_cors import CORS
#from db_schema import *
import json
import datetime
import time
import siphash
import binascii

__author__ = 'Sebastien Chassot'
__author_email__ = 'seba.ptl@sinux.net'

__version__ = "1.0.1"
__copyright__ = ""
__licence__ = "GPL"
__status__ = ""



key = b'0123456789ABCDEF'

app = Flask(__name__)


@app.route("/DrinkingBuddy/sync", methods=['GET'])
def sync():
    """ return drinks catalog


    :return: JSON request tous les capteurs de la classe
    """
    sip = siphash.SipHash_2_4(key)

    now = round(time.time()/60)
    catalog = ['Coca 1.50' , 'Sprite 1.50', 'Rivella 5.95', 'Repas 3.00', 'Biere 2.00'] 

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

#    if request._headers['Content-Type'] == 'application/json':
    dict_req = request.get_json()

    badge = dict_req['Badge']
    product = dict_req['Product']
    time_req = dict_req['Time']

    hash_verif = badge + product + time_req
    for c in hash_verif:
        sipin.update(binascii.a2b_qp(c))

    if dict_req['Hash'] == hex(sipin.hash())[2:].upper():
        print("Cool hash's OK")
    else:
        print("Pas Cool !!!!!!!!!!")
    print(badge + " " + product + " " + time_req + " " + dict_req['Hash'])

# TODO : verify incoming hash

# TODO : compute proper outgoig hash

    ret = {'Melody': "Une melody", 'Message': ['message1', 'message2'], 'Time': now}
    
    hash_str = ret['Melody'] + "".join(ret['Message']) + now.__str__()
    for c in hash_str:
        sip.update(binascii.a2b_qp(c))

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
    messages = ['Username', '44 CHF']

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


# TODO : verify incoming hash

# TODO : compute proper outgoig hash

    ret = {'Melody': "Une melody", 'Message': messages, 'Time': now}
    
    hash_str = ret['Melody'] + "".join(messages) + now.__str__()
    for c in hash_str:
        sipout.update(binascii.a2b_qp(c))

    ret['Hash'] = hex(sipout.hash())[2:].upper()

    return json.dumps(ret)

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int('5000')
    )
