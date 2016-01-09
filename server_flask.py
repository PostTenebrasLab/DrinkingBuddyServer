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

app = Flask(__name__)


@app.route("/drinks/api/sync", methods=['GET'])
def sync():
    """ return drinks catalog


    :return: JSON request tous les capteurs de la classe
    """
    header = "Hello World"
    t = round(time.time())
    catalog = ['Coca 1.50' , 'Sprite 1.50'] 
    h = header
    for i in catalog:
        h += i
    h += t
    for t in h:
        update.hash(t)

    request = {'Header': "Hello World", 'Products': catalog, 'Time': round(time.time()), 'Hash': hash('blabla')}
    
    return json.dumps(request, sort_keys=True)


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

