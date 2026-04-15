from flask import redirect, render_template, request, url_for
from sqlalchemy import or_

from ..drinkingBuddyDB_declarative import Card, User
from .blueprint import _Session, admin_bp


@admin_bp.route('/users')
def users():
    db = _Session()
    return render_template('admin/users.html', users=db.query(User).order_by(User.name).all())


@admin_bp.route('/users/rows')
def users_rows():
    db        = _Session()
    q         = request.args.get('q', '').strip()
    sort      = request.args.get('sort', 'name')
    direction = request.args.get('dir', 'asc')

    query = db.query(User)
    if q:
        query = query.filter(or_(User.name.ilike(f'%{q}%'), User.ldap_user.ilike(f'%{q}%')))

    sort_col = {
        'name':      User.name,
        'balance':   User.balance,
        'ldap_user': User.ldap_user,
        'type':      User.type,
    }.get(sort, User.name)

    if direction == 'desc':
        sort_col = sort_col.desc()

    return render_template('admin/user_rows.html', users=query.order_by(sort_col).all())


@admin_bp.route('/users/<int:user_id>/row')
def user_row(user_id):
    db = _Session()
    return render_template('admin/user_row.html', user=db.get(User, user_id))


@admin_bp.route('/users/<int:user_id>/edit')
def user_edit(user_id):
    db    = _Session()
    user  = db.get(User, user_id)
    cards = db.query(Card).filter(Card.user_id == user_id).order_by(Card.id).all()
    return render_template('admin/user_form.html', user=user, cards=cards)


@admin_bp.route('/users/<int:user_id>', methods=['POST'])
def user_update(user_id):
    db   = _Session()
    user = db.get(User, user_id)
    user.name      = request.form['name']
    user.balance   = round(float(request.form['balance']) * 100)
    user.ldap_user = request.form.get('ldap_user') or None
    user.type      = int(request.form.get('type', 1))
    db.commit()
    return render_template('admin/user_row.html', user=user)


@admin_bp.route('/users/new', methods=['POST'])
def user_create():
    db = _Session()
    user = User(
        name      = request.form['name'],
        balance   = round(float(request.form.get('balance', 0)) * 100),
        type      = int(request.form.get('type', 1)),
        ldap_user = request.form.get('ldap_user') or None,
    )
    db.add(user)
    db.commit()
    return redirect(url_for('admin.users'), 303)


def _cards_response(db, user_id):
    user  = db.get(User, user_id)
    cards = db.query(Card).filter(Card.user_id == user_id).order_by(Card.id).all()
    return render_template('admin/user_cards.html', user=user, cards=cards)


@admin_bp.route('/users/<int:user_id>/cards', methods=['POST'])
def card_create(user_id):
    db = _Session()
    db.add(Card(id=int(request.form['card_id']), user_id=user_id))
    db.commit()
    return _cards_response(db, user_id)


@admin_bp.route('/users/<int:user_id>/cards/<int:card_id>/delete', methods=['POST'])
def card_delete(user_id, card_id):
    db   = _Session()
    card = db.get(Card, card_id)
    if card and card.user_id == user_id:
        db.delete(card)
        db.commit()
    return _cards_response(db, user_id)
