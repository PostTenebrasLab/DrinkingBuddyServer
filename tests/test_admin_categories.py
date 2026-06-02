from sqlalchemy import select

from ptl_buddy_server.models import Category, db


def test_categories_list(client, category):
    r = client.get('/admin/categories')
    assert r.status_code == 200
    assert b'Beverages' in r.data


def test_categories_list_empty(client):
    r = client.get('/admin/categories')
    assert r.status_code == 200


def test_category_edit_form(client, category):
    r = client.get(f'/admin/categories/{category.id}/edit')
    assert r.status_code == 200


def test_category_update(client, category):
    r = client.post(f'/admin/categories/{category.id}', data={'name': 'Drinks'})
    assert r.status_code == 200
    assert b'Drinks' in r.data
    updated = db.session.get(Category, category.id)
    assert updated.name == 'Drinks'


def test_category_update_nonexistent_returns_404(client):
    r = client.post('/admin/categories/9999', data={'name': 'Ghost'})
    assert r.status_code == 404


def test_category_delete(client, category):
    cat_id = category.id
    r = client.post(f'/admin/categories/{cat_id}/delete')
    assert r.status_code == 200
    assert r.data == b''
    assert db.session.get(Category, cat_id) is None


def test_category_delete_nonexistent_returns_404(client):
    r = client.post('/admin/categories/9999/delete')
    assert r.status_code == 404


def test_category_create(client):
    r = client.post('/admin/categories/new', data={'name': 'Snacks'})
    assert r.status_code == 200
    assert b'Snacks' in r.data
    rows = db.session.execute(select(Category).where(Category.name == 'Snacks')).scalars().all()
    assert len(rows) == 1


def test_category_create_persists_name(client):
    client.post('/admin/categories/new', data={'name': 'Hot Drinks'})
    rows = db.session.execute(select(Category).where(Category.name == 'Hot Drinks')).scalars().all()
    assert len(rows) == 1
    assert rows[0].name == 'Hot Drinks'
