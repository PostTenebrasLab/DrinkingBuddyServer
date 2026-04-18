import binascii
import datetime
import logging
import urllib
from collections import OrderedDict
from http import HTTPStatus
from itertools import chain
from typing import TYPE_CHECKING

import siphash
from flask import Flask, Response, abort, request
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import func

from .admin import admin_bp
from .models import Card, Functionality, Item, Locker, Terminal, Transaction, TransactionItem, User, db

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Never

    from sqlalchemy.schema import Column


    JsonObject = dict[str, Any]


logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config.from_prefixed_env()
db.init_app(app)
app.register_blueprint(admin_bp)


def datetime_now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


def datetime_seconds(datetime: datetime.datetime) -> int:
    return round(datetime.timestamp())


def abort_unauthorized(message: str) -> Never:
    raise abort(Response(message, HTTPStatus.UNAUTHORIZED, {'WWW-Authenticate': 'Basic'}))


def basic_auth() -> Terminal:
    authorization = request.authorization
    if authorization is None:
        abort_unauthorized('auth-none')

    if authorization.type != 'basic':
        abort_unauthorized(f'auth-type: {authorization.type}')

    username = authorization.username
    password = authorization.password
    terminals = db.session.query(Terminal, Terminal.id)
    terminals = terminals.filter(Terminal.name == username, Terminal.key == password)
    terminal = terminals.one_or_none()
    if terminal is None:
        abort_unauthorized(f'auth-credentials: {username}:{password}')

    return terminal


def ceil_div(n: int, d: int) -> int:
    return -(n // -d)


def int_to_bytes(i: int) -> bytes:
    bytes_count = ceil_div(i.bit_length(), 8)
    return i.to_bytes(bytes_count)


def int_to_opaque_str(i: int) -> str:
    return urllib.parse.quote_from_bytes(int_to_bytes(i))


@app.route('/search', methods=['GET'])
def search() -> JsonObject:
    _terminal = basic_auth()

    query_str = request.args['q']

    item = db.session.query(Item, Item.id, Item.name, Item.price).filter(Item.barcode == query_str).one_or_none()
    if item is not None:
        return OrderedDict(
            type='Item',
            id=int_to_opaque_str(item.id),
            name=item.name,
            value=item.price,
        )

    # query can't be constructed from request.args for non-UTF-8 byte sequences
    query_bytes = urllib.parse.parse_qs(request.query_string, keep_blank_values=True)[b'q'][0]
    query_int = int.from_bytes(query_bytes)

    try:
        users = db.session.query(User, User.id, User.name, User.balance)
        users = users.join(Card, User.id == Card.user_id)
        users = users.filter(Card.id == query_int)
        user = users.one_or_none()
    except OverflowError:
        user = None

    if user is not None:
        return OrderedDict(
            type='User',
            id=int_to_opaque_str(user.id),
            name=user.name,
            balance=user.balance,
        )

    raise abort(HTTPStatus.NOT_FOUND, f'q={query_str}|{query_bytes.hex()}')


@app.route('/transact', methods=['POST'])
def transact() -> JsonObject:
    _terminal = basic_auth()

    # trigger an HTTP 400 error if a parameter is missing
    request.args['user']
    request.args['item']

    # query can't be constructed from request.args for non-UTF-8 byte sequences
    query = urllib.parse.parse_qs(request.query_string)
    user_id = int.from_bytes(query[b'user'][0])
    item_id = int.from_bytes(query[b'item'][0])

    user = db.session.query(User).filter(User.id == user_id).with_for_update().one()
    item = db.session.query(Item).filter(Item.id == item_id).with_for_update().one()

    balance_new = user.balance - item.price
    if item.price > 0 and balance_new < 0:
        raise abort(HTTPStatus.PAYMENT_REQUIRED, 'Too poor!')

    now = datetime_now()
    user.balance = balance_new
    item.quantity -= 1

    transaction = Transaction(user=user, date=now, value=1)
    db.session.add(transaction)

    transaction_item = TransactionItem(
        transaction=transaction,
        date=now,
        quantity=1,
        price_per_item=item.price,
        canceled_date=None,
        element_id=item.id,
    )
    db.session.add(transaction_item)

    db.session.commit()

    return OrderedDict(
        id=urllib.parse.quote_from_bytes(int_to_bytes(user.id)),
        name=user.name,
        balance=user.balance,
    )


def get_terminal(*columns: Column) -> Terminal:
    terminal_id = request.json['Tid']
    return db.session.query(Terminal, Terminal.key, *columns).filter(Terminal.id == terminal_id).one()


def compute_hash(terminal: Terminal, *strings: Iterable[str]) -> str:
    hasher = siphash.SipHash_2_4(terminal.key.encode())
    for i in chain.from_iterable(strings):
        hasher.update(binascii.a2b_qp(i))
    return f'{hasher.hash():X}'.zfill(16)


@app.route('/sync', methods=['POST'])
def sync() -> JsonObject:
    """Return drinks catalog based on terminal id.

    curl --json '{"Tid":"1"}' http://localhost:5000/sync

    :return: JSON request toutes les categories accessible a un terminal
    """
    terminal = get_terminal(Terminal.id)
    header = 'DrinkingBuddy'

    items = db.session.query(Item, Item.id, Item.name, Item.price)
    items = items.join(Functionality, Functionality.category_id == Item.category_id)
    items = items.filter(Functionality.terminal_id == terminal.id, Item.quantity > 0)
    items = tuple(items)

    now = datetime_seconds(datetime_now())
    return dict(
        Header=header,
        Products=[[i.id, i.name, f'{i.price/100:.2f}'] for i in items],
        Time=now,
        Hash=compute_hash(
            terminal,
            header,
            chain.from_iterable(chain(str(i.id), i.name, f'{i.price/100:.2f}') for i in items),
            str(now),
        ),
    )


@app.route('/gettime', methods=['POST'])
def gettime() -> JsonObject:
    """Return drinks catalog based on terminal id.

    curl --json '{"Tid":"1"}' http://localhost:5000/gettime

    :return: JSON request toutes les categories accessible a un terminal
    """
    terminal = get_terminal()

    header = 'DrinkingBuddy'
    now = datetime_seconds(datetime_now())
    return dict(
        Header=header,
        Melody='c1',
        Time=now,
        Hash=compute_hash(terminal, header, str(now)),
    )


# is this used? it crashes when badge is unknown
@app.route('/user', methods=['POST'])
def get_user() -> JsonObject:
    """Get user request.

    :return: JSON
    """
    terminal = get_terminal()
    badge = request.json['Badge']

    hash_should = compute_hash(terminal, badge, str(request.json.get('Time', 0)))
    logger.debug('/user %s, %s', request.json['Hash'], hash_should)

    users = db.session.query(User, User.name)
    users = users.join(Card, User.id == Card.user_id)
    users = users.filter(Card.id == int(badge, 16), User.type == 1)
    user = users.one_or_none()
    if user is None:
        message = ['ERROR', 'UNKNOWN USER']
        melody = 'c5'
    else:
        # TEMP the 100/100 should be replaced by group ID or other info
        message = [user.name, f'{100/100:.2f}']
        melody = 'a1c1a1c1a1c1a1c1'

    now = datetime_seconds(datetime_now())
    return dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, user.name, str(now)),
    )


@app.route('/add', methods=['POST'])
def add() -> JsonObject:
    """Add request.

    :return: JSON
    """
    terminal = get_terminal()
    badge = request.json['Badge']

    product = request.json.get('Product')
    barcode = request.json.get('Barcode')
    if product:
        item_selector = product
        item_filter = Item.id == int(product)
    elif barcode:
        item_selector = barcode
        item_filter = Item.barcode == barcode.rstrip('\r\n')
    else:
        raise abort(HTTPStatus.BAD_REQUEST, {'ERROR': 'Missing barcode or product ID'})

    req_hash = compute_hash(terminal, badge, str(item_selector), str(request.json['Time']))
    if request.json['Hash'] != req_hash:
        raise abort(HTTPStatus.BAD_REQUEST, {'DrinkingBuddy error': f'Hash error {req_hash}'})

    now = datetime_now()

    users = db.session.query(User, User.id, User.type)
    users = users.join(Card, Card.user_id == User.id)
    users = users.filter(Card.id == int(badge, 16))
    user = users.one()

    if user.type != 1:
        melody = 'b2c3b2'
        message = ['ERROR', 'User cannot add items']
    else:
        item_count = request.json.get('Item_count')
        item_count = int(item_count) if item_count else 1

        item = db.session.query(Item).filter(item_filter).one()
        item.quantity += item_count

        transaction = Transaction(date=now, value=1, user=user)
        db.session.add(transaction)

        transaction_item = TransactionItem(
            date=now,
            quantity=-item_count,
            price_per_item=item.price,
            canceled_date=None,
            element_id=item.id,
            transaction=transaction,
        )
        db.session.add(transaction_item)

        db.session.commit()

        melody = 'a1a1a1b1b1f1g1'
        message = ['Successfull transaction', 'Have a nice day']

    now = str(datetime_seconds(now))
    return dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, chain.from_iterable(message), now),
    )


@app.route('/buy', methods=['POST'])
def buy() -> JsonObject:
    """Buy request.

    curl --json '{"Tid":"1","Badge":"4285702E","Product":"5","Time":"53677","Hash":"4527E4199D78DC12"}' http://localhost:5000/buy

    :return: JSON request tous les capteurs de la classe
    """
    terminal = get_terminal()
    badge = request.json['Badge']

    product = request.json.get('Product')
    barcode = request.json.get('Barcode')
    if product:
        item_selector = product
        item_filter = Item.id == int(product)
    elif barcode:
        item_selector = barcode
        item_filter = Item.barcode == barcode.strip()
    else:
        abort(HTTPStatus.BAD_REQUEST, {'DrinkingBuddy buy error': 'Missing barcode or product ID'})

    hash_should = compute_hash(terminal, badge, str(item_selector), str(request.json['Time']))
    logger.debug('/buy %s, %s', request.json['Hash'], hash_should)

    user = db.session.query(User).join(Card, Card.user_id == User.id).filter(Card.id == int(badge, 16)).one()
    item = db.session.query(Item).filter(item_filter).one()

    now = datetime_now()

    if item.quantity < 1 and product:
        melody = 'b2c3b2'
        message = ['ERROR', 'Not in stock']
        item_price = None
    elif user.balance < item.price:
        melody = 'b2c3b2'
        message = ['ERROR', 'Too poor!']
        item_price = None
    else:
        item.quantity -= 1
        user.balance -= item.price

        transaction = Transaction(date=now, value=1, user=user)
        db.session.add(transaction)

        transaction_item = TransactionItem(
            date=now,
            quantity=1,
            price_per_item=item.price,
            canceled_date=None,
            element_id=item.id,
            transaction=transaction,
        )
        db.session.add(transaction_item)

        db.session.commit()

        melody = 'a1b1c1d1e1f1g1'
        message = ['Successfull transaction', item.name]
        item_price = item.price

    now = str(datetime_seconds(now))
    response = dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, chain.from_iterable(message), now),
    )
    if item_price is not None:
        response['ItemPrice'] = item_price
    return response


@app.route('/balance', methods=['POST'])
def get_balance() -> JsonObject:
    """Get balance request."""
    terminal = get_terminal()
    badge = request.json['Badge']

    hash_should = compute_hash(terminal, badge, str(request.json['Time']))
    logger.debug('/balance %s, %s', request.json['Hash'], hash_should)

    users = db.session.query(User, User.name, User.balance)
    users = users.join(Card, User.id == Card.user_id)
    users = users.filter(Card.id == int(badge, 16))
    user = users.one_or_none()

    if user is None:
        melody = 'c5'
        message = ['ERROR', 'UNKNOWN USER']
    else:
        melody = 'a1c1a1c1a1c1a1c1'
        message = [user.name, f'{user.balance/100:.2f}']

    now = datetime_seconds(datetime_now())
    return dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, chain.from_iterable(message), str(now)),
    )


@app.route('/total', methods=['GET'])
def total() -> list[str]:
    date_from = request.args['from']
    date_to = request.args['to']

    query = db.session.query(
        func.sum(Transaction.value).label('sum'),
        func.count(Transaction.id).label('count'),
    ).filter(Transaction.date.between(date_from, date_to))

    return [f'{i.count} {i.sum}' for i in query]


@app.route('/locker', methods=['POST'])
def get_locker() -> JsonObject:
    """Get locker IDs that can be opened by userID matching sent cardID."""
    terminal = get_terminal()
    badge = request.json['Badge']

    if request.json['Hash'] != compute_hash(terminal, badge, request.json['Time']):
        melody = 'c5'
        message = ['ERROR', 'HASH DOES NOT MATCH']
    else:
        lockers = db.session.query(Locker, Locker.lockername)
        lockers = lockers.join(User, Locker.user_id == User.id)
        lockers = lockers.join(Card, User.id == Card.user_id)
        lockers = lockers.filter(Card.id == int(badge, 16))
        if lockers.count() == 0:
            melody = 'c5'
            message = ['ERROR', 'UNKNOWN USER, CARD OR LOCKER']
        else:
            melody = 'a1a1a1c1c1c1a1c1'
            message = [str(locker.lockername) for locker in lockers]

    now = datetime_seconds(datetime_now())
    return dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, chain.from_iterable(message), str(now)),
    )


@app.route('/foodcount', methods=['GET'])
def get_food() -> JsonObject:
    food_item_id = 5
    now = datetime_now()

    transactions = db.session.query(TransactionItem)
    transactions = transactions.filter(TransactionItem.element_id == food_item_id)
    transactions = transactions.filter(TransactionItem.date >= now.today())
    transactions = transactions.filter(not TransactionItem.canceled)
    count = transactions.count()

    now = datetime_seconds(now)
    return dict(
        Message=['Food bought today', count],
        Melody='a2',
        Time=now,
        Hash='Bidon',
    )


@app.route('/beverages', methods=['GET'])
def get_beverages() -> list[JsonObject]:
    return [serialize(i) for i in db.session.query(Item).all()]


@app.route('/beverages/<barcode>', methods=['GET'])
def get_beverage_barcode(barcode: str) -> JsonObject:
    return serialize(db.session.query(Item).filter(Item.barcode == barcode).one())


@app.route('/beverages', methods=['POST'])
def post_beverages() -> JsonObject:
    beverage = Item(name=request.json['name'], quantity=request.json['quantity'])
    db.session.add(beverage)
    db.session.commit()
    return serialize(beverage)


@app.route('/addcents', methods=['POST'])
def addcents() -> JsonObject:
    """/addcents request.

    curl --json '{"Tid":"1","Badge":"4285702E","Cents":"5","Time":"53677","Hash":"4527E4199D78DC12"}' http://localhost:5000/addcents

    :return: JSON request tous les capteurs de la classe
    """
    terminal = get_terminal()
    badge = request.json['Badge']

    cents = request.json['Cents']

    if not cents:
        raise abort(HTTPStatus.BAD_REQUEST, {'DrinkingBuddy addcents error': 'Missing cents'})
    cents_int = int(cents)
    if cents_int < 0:
        raise abort(HTTPStatus.BAD_REQUEST, {'DrinkingBuddy addcents error': 'cents cannot be negative'})

    sent_hash = request.json['Hash']
    req_hash = compute_hash(terminal, badge, str(cents), str(request.json['Time']))
    if sent_hash != req_hash:
        raise abort(HTTPStatus.BAD_REQUEST, {'DrinkingBuddy error': f'Hash error {req_hash}  {sent_hash}'})

    users = db.session.query(User)
    users = users.join(Card, Card.user_id == User.id)
    users = users.filter(Card.id == int(badge, 16))
    user = users.one()
    user.balance += cents_int

    now = datetime_now()
    transaction = Transaction(date=now, value=1, user=user)
    db.session.add(transaction)

    transaction_item = TransactionItem(
        date=now,
        quantity=cents_int,
        price_per_item=-1,
        canceled_date=None,
        element_id=1000,
        transaction=transaction,
    )
    db.session.add(transaction_item)

    db.session.commit()

    melody = 'a1b1c1d1e1f1g1'
    message = ['Successfull add cents', str(cents)]
    now = str(datetime_seconds(now))
    return dict(
        Melody=melody,
        Message=message,
        Time=now,
        Hash=compute_hash(terminal, melody, chain.from_iterable(message), now),
    )


def serialize(model: Any) -> JsonObject:
    return {(key := column.key): getattr(model, key) for column in class_mapper(model.__class__).columns}
