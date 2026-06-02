from sqlalchemy import select

from ptl_buddy_server.models import Item, db


def test_items_list(client, item):
    r = client.get('/admin/items')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_items_list_empty(client):
    r = client.get('/admin/items')
    assert r.status_code == 200


def test_items_rows_all(client, item):
    r = client.get('/admin/items/rows')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_items_rows_search_match(client, item):
    r = client.get('/admin/items/rows?q=Cola')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_items_rows_search_no_match(client, item):
    r = client.get('/admin/items/rows?q=Nonexistent')
    assert r.status_code == 200
    assert b'Cola' not in r.data


def test_items_rows_search_by_barcode(client, item):
    r = client.get('/admin/items/rows?q=12345')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_items_rows_sort_price_asc(client, item):
    r = client.get('/admin/items/rows?sort=price&dir=asc')
    assert r.status_code == 200


def test_items_rows_sort_price_desc(client, item):
    r = client.get('/admin/items/rows?sort=price&dir=desc')
    assert r.status_code == 200


def test_items_rows_sort_unknown_defaults_to_name(client, item):
    r = client.get('/admin/items/rows?sort=nonexistent')
    assert r.status_code == 200


def test_items_rows_category_filter_match(client, item, category):
    r = client.get(f'/admin/items/rows?has_cat_filter=1&category_id={category.id}')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_items_rows_category_filter_no_selection_returns_empty(client, item):
    r = client.get('/admin/items/rows?has_cat_filter=1')
    assert r.status_code == 200
    assert b'Cola' not in r.data


def test_items_rows_category_filter_wrong_category(client, item):
    r = client.get('/admin/items/rows?has_cat_filter=1&category_id=9999')
    assert r.status_code == 200
    assert b'Cola' not in r.data


def test_item_row_existing(client, item):
    r = client.get(f'/admin/items/{item.id}/row')
    assert r.status_code == 200


def test_item_edit_form(client, item):
    r = client.get(f'/admin/items/{item.id}/edit')
    assert r.status_code == 200


def test_item_update(client, item, category):
    r = client.post(f'/admin/items/{item.id}', data={
        'name': 'Pepsi',
        'quantity': '5',
        'minquantity': '1',
        'price': '1.50',
        'barcode': '67890',
        'category_id': str(category.id),
    })
    assert r.status_code == 200
    assert b'Pepsi' in r.data


def test_item_update_price_stored_as_cents(client, item, category):
    client.post(f'/admin/items/{item.id}', data={
        'name': 'Cola',
        'quantity': '10',
        'minquantity': '2',
        'price': '2.50',
        'barcode': '',
        'category_id': str(category.id),
    })
    updated = db.session.get(Item, item.id)
    assert updated.price == 250


def test_item_update_empty_barcode_becomes_none(client, item, category):
    client.post(f'/admin/items/{item.id}', data={
        'name': 'Cola',
        'quantity': '10',
        'minquantity': '2',
        'price': '1.50',
        'barcode': '',
        'category_id': str(category.id),
    })
    updated = db.session.get(Item, item.id)
    assert updated.barcode is None


def test_item_update_nonexistent_returns_404(client):
    r = client.post('/admin/items/9999', data={
        'name': 'Ghost',
        'quantity': '0',
        'minquantity': '0',
        'price': '1.00',
        'category_id': '1',
    })
    assert r.status_code == 404


def test_item_delete(client, item):
    item_id = item.id
    r = client.post(f'/admin/items/{item_id}/delete')
    assert r.status_code == 200
    assert r.data == b''
    assert db.session.get(Item, item_id) is None


def test_item_delete_nonexistent_returns_404(client):
    r = client.post('/admin/items/9999/delete')
    assert r.status_code == 404


def test_item_create(client, category):
    r = client.post('/admin/items/new', data={
        'name': 'Water',
        'quantity': '20',
        'minquantity': '5',
        'price': '0.50',
        'barcode': 'WATER01',
        'category_id': str(category.id),
    })
    assert r.status_code == 303
    rows = db.session.execute(select(Item).where(Item.name == 'Water')).scalars().all()
    assert len(rows) == 1
    assert rows[0].price == 50


def test_item_create_optional_fields_default_to_zero(client, category):
    r = client.post('/admin/items/new', data={
        'name': 'Mystery',
        'category_id': str(category.id),
    })
    assert r.status_code == 303
    rows = db.session.execute(select(Item).where(Item.name == 'Mystery')).scalars().all()
    assert rows[0].quantity == 0
    assert rows[0].price == 0


def test_item_create_empty_barcode_becomes_none(client, category):
    client.post('/admin/items/new', data={
        'name': 'NoBarcodeItem',
        'quantity': '1',
        'minquantity': '0',
        'price': '1.00',
        'barcode': '',
        'category_id': str(category.id),
    })
    rows = db.session.execute(select(Item).where(Item.name == 'NoBarcodeItem')).scalars().all()
    assert rows[0].barcode is None
