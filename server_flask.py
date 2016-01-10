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



#eng = create_engine("sqlite:////.db")
#conn = eng.connect()
#Session = sessionmaker(bind=eng)
#session = Session()

key = b'0123456789ABCDEF'
sip = siphash.SipHash_2_4(key)

app = Flask(__name__)


@app.route("/drinks/api/sync", methods=['GET'])
def sync():
    """ return drinks catalog


    :return: JSON request tous les capteurs de la classe
    """
    now = round(time.time()/60)
    catalog = ['Coca 1.50' , 'Sprite 1.50'] 

    request = {'Header': "Hello World", 'Products': catalog, 'Time': now}

    hash_str = request['Header'] + "".join(catalog) + now.__str__()
    request['Hash'] = sip.hash()
    
    return json.dumps(request)


@app.route("/drinks/api/buy", methods=['POST'])
def buy():
    """ buy request


    :return: JSON request tous les capteurs de la classe
    """

    return json.dumps(res, sort_keys=True)


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int('5000')
    )
