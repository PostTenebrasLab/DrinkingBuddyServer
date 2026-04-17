from flask import render_template, request

from ..models import Category
from .blueprint import _Session, admin_bp


@admin_bp.route('/categories')
def categories():
    db = _Session()
    return render_template('admin/categories.html',
                           categories=db.query(Category).order_by(Category.name).all())


@admin_bp.route('/categories/<int:category_id>/edit')
def category_edit(category_id):
    db = _Session()
    return render_template('admin/category_form.html', category=db.get(Category, category_id))


@admin_bp.route('/categories/<int:category_id>', methods=['POST'])
def category_update(category_id):
    db       = _Session()
    category = db.get(Category, category_id)
    category.name = request.form['name']
    db.commit()
    return render_template('admin/category_row.html', category=category)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def category_delete(category_id):
    db = _Session()
    db.delete(db.get(Category, category_id))
    db.commit()
    return ''


@admin_bp.route('/categories/new', methods=['POST'])
def category_create():
    db  = _Session()
    cat = Category(name=request.form['name'])
    db.add(cat)
    db.commit()
    return render_template('admin/category_row.html', category=cat)
