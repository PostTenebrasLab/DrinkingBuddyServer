from flask import redirect, render_template, request, url_for
from sqlalchemy import false as sa_false, or_

from ..models import Category, Item
from .blueprint import _Session, admin_bp


@admin_bp.route('/items')
def items():
    db = _Session()
    all_items  = db.query(Item).outerjoin(Category).order_by(Item.name).all()
    categories = db.query(Category).order_by(Category.name).all()
    return render_template('admin/items.html', items=all_items, categories=categories)


@admin_bp.route('/items/rows')
def items_rows():
    db        = _Session()
    q         = request.args.get('q', '').strip()
    sort      = request.args.get('sort', 'name')
    direction = request.args.get('dir', 'asc')

    query = db.query(Item).outerjoin(Category)
    if q:
        query = query.filter(or_(Item.name.ilike(f'%{q}%'), Item.barcode.ilike(f'%{q}%')))
    if request.args.get('has_cat_filter'):
        category_ids = [int(x) for x in request.args.getlist('category_id') if x.isdigit()]
        query = query.filter(Item.category_id.in_(category_ids)) if category_ids else query.filter(sa_false())

    sort_col = {
        'name':        Item.name,
        'category':    Category.name,
        'quantity':    Item.quantity,
        'minquantity': Item.minquantity,
        'price':       Item.price,
        'barcode':     Item.barcode,
    }.get(sort, Item.name)

    if direction == 'desc':
        sort_col = sort_col.desc()

    return render_template('admin/item_rows.html', items=query.order_by(sort_col).all())


@admin_bp.route('/items/<int:item_id>/row')
def item_row(item_id):
    db = _Session()
    return render_template('admin/item_row.html', item=db.get(Item, item_id))


@admin_bp.route('/items/<int:item_id>/edit')
def item_edit(item_id):
    db = _Session()
    categories = db.query(Category).order_by(Category.name).all()
    return render_template('admin/item_form.html', item=db.get(Item, item_id), categories=categories)


@admin_bp.route('/items/<int:item_id>', methods=['POST'])
def item_update(item_id):
    db   = _Session()
    item = db.get(Item, item_id)
    item.name        = request.form['name']
    item.quantity    = int(request.form['quantity'])
    item.minquantity = int(request.form['minquantity'])
    item.price       = round(float(request.form['price']) * 100)
    item.barcode     = request.form.get('barcode') or None
    item.category_id = int(request.form['category_id'])
    db.commit()
    return render_template('admin/item_row.html', item=item)


@admin_bp.route('/items/<int:item_id>/delete', methods=['POST'])
def item_delete(item_id):
    db = _Session()
    db.delete(db.get(Item, item_id))
    db.commit()
    return ''


@admin_bp.route('/items/new', methods=['POST'])
def item_create():
    db = _Session()
    item = Item(
        name        = request.form['name'],
        quantity    = int(request.form.get('quantity', 0)),
        minquantity = int(request.form.get('minquantity', 0)),
        price       = round(float(request.form.get('price', 0)) * 100),
        barcode     = request.form.get('barcode') or None,
        category_id = int(request.form['category_id']),
    )
    db.add(item)
    db.commit()
    return redirect(url_for('admin.items'), 303)
