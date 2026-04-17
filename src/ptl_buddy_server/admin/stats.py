from flask import render_template, request
from sqlalchemy import false as sa_false, func

from ..models import Category, Item, TransactionItem
from .blueprint import _Session, admin_bp


def _stats_query(db, q='', category_ids=None, has_cat_filter=False,
                 sort='qty', direction='desc', date_from='', date_to=''):
    qty_col     = func.sum(TransactionItem.quantity).label('total_qty')
    revenue_col = func.sum(TransactionItem.quantity * TransactionItem.price_per_item).label('total_revenue')
    query = (db.query(Item, qty_col, revenue_col)
               .join(TransactionItem, TransactionItem.element_id == Item.id)
               .outerjoin(Category, Item.category_id == Category.id)
               .filter(TransactionItem.canceled.isnot(True))
               .filter(Item.id < 999)
               .group_by(Item.id))
    if q:
        query = query.filter(Item.name.ilike(f'%{q}%'))
    if has_cat_filter:
        query = query.filter(Item.category_id.in_(category_ids)) if category_ids else query.filter(sa_false())
    if date_from:
        query = query.filter(TransactionItem.date >= date_from)
    if date_to:
        query = query.filter(TransactionItem.date <= date_to)
    sort_col = {
        'name':     Item.name,
        'qty':      qty_col,
        'revenue':  revenue_col,
        'category': Category.name,
    }.get(sort, qty_col)
    return query.order_by(sort_col.desc() if direction == 'desc' else sort_col.asc()).all()


def _stats_chart_data(db, q='', category_ids=None, has_cat_filter=False, date_from='', date_to=''):
    date_label = func.strftime('%Y-%m-%d', TransactionItem.date).label('day')
    qty_col    = func.sum(TransactionItem.quantity).label('total_qty')
    query = (db.query(date_label, qty_col)
               .join(Item, TransactionItem.element_id == Item.id)
               .filter(TransactionItem.canceled.isnot(True))
               .filter(Item.id < 999)
               .group_by('day').order_by('day'))
    if q:
        query = query.filter(Item.name.ilike(f'%{q}%'))
    if has_cat_filter:
        query = query.filter(Item.category_id.in_(category_ids)) if category_ids else query.filter(sa_false())
    if date_from:
        query = query.filter(TransactionItem.date >= date_from)
    if date_to:
        query = query.filter(TransactionItem.date <= date_to)
    rows = query.all()
    return {'labels': [r.day for r in rows], 'values': [r.total_qty for r in rows]}


@admin_bp.route('/stats')
def stats():
    db         = _Session()
    categories = db.query(Category).order_by(Category.name).all()
    rows       = _stats_query(db, sort='qty', direction='desc')
    chart      = _stats_chart_data(db)
    return render_template('admin/stats.html', rows=rows, chart=chart, categories=categories)


@admin_bp.route('/stats/rows')
def stats_rows():
    db             = _Session()
    q              = request.args.get('q', '').strip()
    has_cat_filter = bool(request.args.get('has_cat_filter'))
    category_ids   = [int(x) for x in request.args.getlist('category_id') if x.isdigit()]
    sort           = request.args.get('sort', 'qty')
    direction      = request.args.get('dir', 'desc')
    date_from      = request.args.get('date_from', '').strip()
    date_to        = request.args.get('date_to', '').strip()
    rows  = _stats_query(db, q, category_ids, has_cat_filter, sort, direction, date_from, date_to)
    chart = _stats_chart_data(db, q, category_ids, has_cat_filter, date_from, date_to)
    return render_template('admin/stats_rows.html', rows=rows, chart=chart)
