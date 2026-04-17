from flask import render_template, request
from sqlalchemy.orm import contains_eager, joinedload

from ..models import Transaction, User
from .blueprint import _Session, admin_bp

_PER_PAGE = 50


@admin_bp.route('/transactions')
def transactions():
    db       = _Session()
    page     = max(1, int(request.args.get('page', 1)))
    total    = db.query(Transaction).count()
    txns     = (db.query(Transaction)
                .options(joinedload(Transaction.user))
                .order_by(Transaction.date.desc())
                .offset((page - 1) * _PER_PAGE)
                .limit(_PER_PAGE)
                .all())
    return render_template('admin/transactions.html',
                           transactions=txns, page=page, total=total, per_page=_PER_PAGE)


@admin_bp.route('/transactions/rows')
def transactions_rows():
    db        = _Session()
    q         = request.args.get('q', '').strip()
    sort      = request.args.get('sort', 'date')
    direction = request.args.get('dir', 'desc')
    page      = max(1, int(request.args.get('page', 1)))

    query = (db.query(Transaction)
             .outerjoin(User, Transaction.user_id == User.id)
             .options(contains_eager(Transaction.user)))

    if q:
        query = query.filter(User.name.ilike(f'%{q}%'))

    sort_col = {
        'date':  Transaction.date,
        'user':  User.name,
        'value': Transaction.value,
    }.get(sort, Transaction.date)

    if direction == 'desc':
        sort_col = sort_col.desc()

    total = query.count()
    txns  = query.order_by(sort_col).offset((page - 1) * _PER_PAGE).limit(_PER_PAGE).all()
    return render_template('admin/transaction_rows.html',
                           transactions=txns, page=page, total=total, per_page=_PER_PAGE)
