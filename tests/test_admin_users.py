from sqlalchemy import select

from ptl_buddy_server.models import Card, User, db


def test_users_list(client, user):
    r = client.get('/admin/users')
    assert r.status_code == 200
    assert b'Alice' in r.data


def test_users_list_empty(client):
    r = client.get('/admin/users')
    assert r.status_code == 200


def test_users_rows_all(client, user):
    r = client.get('/admin/users/rows')
    assert r.status_code == 200
    assert b'Alice' in r.data


def test_users_rows_search_match(client, user):
    r = client.get('/admin/users/rows?q=Alice')
    assert r.status_code == 200
    assert b'Alice' in r.data


def test_users_rows_search_no_match(client, user):
    r = client.get('/admin/users/rows?q=Bob')
    assert r.status_code == 200
    assert b'Alice' not in r.data


def test_users_rows_sort_balance_desc(client, user):
    r = client.get('/admin/users/rows?sort=balance&dir=desc')
    assert r.status_code == 200


def test_users_rows_sort_unknown_defaults_to_name(client, user):
    r = client.get('/admin/users/rows?sort=invalid')
    assert r.status_code == 200


def test_user_row(client, user):
    r = client.get(f'/admin/users/{user.id}/row')
    assert r.status_code == 200


def test_user_edit_form(client, user):
    r = client.get(f'/admin/users/{user.id}/edit')
    assert r.status_code == 200


def test_user_update(client, user):
    r = client.post(f'/admin/users/{user.id}', data={
        'name': 'Alicia',
        'balance': '15.00',
        'type': '1',
        'ldap_user': '',
    })
    assert r.status_code == 200
    assert b'Alicia' in r.data


def test_user_update_balance_stored_as_cents(client, user):
    client.post(f'/admin/users/{user.id}', data={
        'name': 'Alice',
        'balance': '12.34',
        'type': '1',
    })
    updated = db.session.get(User, user.id)
    assert updated.balance == 1234


def test_user_update_empty_ldap_becomes_none(client, user):
    client.post(f'/admin/users/{user.id}', data={
        'name': 'Alice',
        'balance': '10.00',
        'type': '1',
        'ldap_user': '',
    })
    updated = db.session.get(User, user.id)
    assert updated.ldap_user is None


def test_user_update_nonexistent_returns_404(client):
    r = client.post('/admin/users/9999', data={
        'name': 'Ghost',
        'balance': '0',
        'type': '1',
    })
    assert r.status_code == 404


def test_user_create(client):
    r = client.post('/admin/users/new', data={
        'name': 'Bob',
        'balance': '5.00',
        'type': '2',
        'ldap_user': 'bob',
    })
    assert r.status_code == 303
    rows = db.session.execute(select(User).where(User.name == 'Bob')).scalars().all()
    assert len(rows) == 1
    assert rows[0].balance == 500


def test_user_create_default_balance_is_zero(client):
    client.post('/admin/users/new', data={'name': 'Charlie', 'type': '1'})
    rows = db.session.execute(select(User).where(User.name == 'Charlie')).scalars().all()
    assert rows[0].balance == 0


def test_user_create_empty_ldap_becomes_none(client):
    client.post('/admin/users/new', data={'name': 'Dave', 'type': '1', 'ldap_user': ''})
    rows = db.session.execute(select(User).where(User.name == 'Dave')).scalars().all()
    assert rows[0].ldap_user is None


def test_card_create(client, user):
    r = client.post(f'/admin/users/{user.id}/cards', data={'card_id': '42'})
    assert r.status_code == 200
    cards = db.session.execute(select(Card).where(Card.user_id == user.id)).scalars().all()
    assert any(c.id == 42 for c in cards)


def test_card_create_non_integer_id_returns_error(client, user):
    # int(request.form['card_id']) crashes if the value isn't numeric
    r = client.post(f'/admin/users/{user.id}/cards', data={'card_id': 'notanint'})
    assert r.status_code == 400


def test_card_delete(client, user):
    card = Card(id=99, user_id=user.id)
    db.session.add(card)
    db.session.commit()
    r = client.post(f'/admin/users/{user.id}/cards/99/delete')
    assert r.status_code == 200
    assert db.session.get(Card, 99) is None


def test_card_delete_wrong_user_does_not_delete(client, user):
    other = User(name='Eve', balance=0, type=1)
    db.session.add(other)
    db.session.commit()
    card = Card(id=77, user_id=other.id)
    db.session.add(card)
    db.session.commit()
    # Try to delete Eve's card via Alice's user_id — should be ignored
    r = client.post(f'/admin/users/{user.id}/cards/77/delete')
    assert r.status_code == 200
    assert db.session.get(Card, 77) is not None


def test_card_delete_nonexistent_card_is_noop(client, user):
    r = client.post(f'/admin/users/{user.id}/cards/9999/delete')
    assert r.status_code == 200
