from flask import render_template
from sqlalchemy import func

from ..models import Item, Transaction, User
from .blueprint import _Session, admin_bp


@admin_bp.route('/')
def dashboard():
    db = _Session()
    item_count        = db.query(Item).filter(Item.id < 999).count()
    user_count        = db.query(User).count()
    transaction_count = db.query(Transaction).count()
    total_balance     = db.query(func.sum(User.balance)).scalar() or 0
    low_stock = (db.query(Item)
                 .filter(Item.id < 999, Item.minquantity.isnot(None), Item.minquantity >= 0, Item.quantity <= Item.minquantity)
                 .order_by(Item.name)
                 .all())
    return render_template('admin/dashboard.html',
                           item_count=item_count,
                           user_count=user_count,
                           transaction_count=transaction_count,
                           total_balance=total_balance,
                           low_stock=low_stock)
