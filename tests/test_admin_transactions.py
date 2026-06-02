def test_transactions_empty(client):
    r = client.get('/admin/transactions')
    assert r.status_code == 200


def test_transactions_with_data(client, transaction):
    r = client.get('/admin/transactions')
    assert r.status_code == 200


def test_transactions_page_1(client, transaction):
    r = client.get('/admin/transactions?page=1')
    assert r.status_code == 200


def test_transactions_page_below_1_clamped_to_1(client):
    r = client.get('/admin/transactions?page=0')
    assert r.status_code == 200


def test_transactions_invalid_page_returns_error(client):
    # int('abc') raises ValueError — should return 400, not crash with 500
    r = client.get('/admin/transactions?page=abc')
    assert r.status_code == 400


def test_transactions_rows_empty(client):
    r = client.get('/admin/transactions/rows')
    assert r.status_code == 200


def test_transactions_rows_with_data(client, transaction):
    r = client.get('/admin/transactions/rows')
    assert r.status_code == 200


def test_transactions_rows_search_match(client, transaction):
    r = client.get('/admin/transactions/rows?q=Alice')
    assert r.status_code == 200


def test_transactions_rows_search_no_match(client, transaction):
    r = client.get('/admin/transactions/rows?q=Nobody')
    assert r.status_code == 200


def test_transactions_rows_sort_by_user_asc(client, transaction):
    r = client.get('/admin/transactions/rows?sort=user&dir=asc')
    assert r.status_code == 200


def test_transactions_rows_sort_by_date_desc(client, transaction):
    r = client.get('/admin/transactions/rows?sort=date&dir=desc')
    assert r.status_code == 200


def test_transactions_rows_invalid_page_returns_error(client):
    r = client.get('/admin/transactions/rows?page=xyz')
    assert r.status_code == 400


def test_transactions_rows_page_below_1_clamped(client):
    r = client.get('/admin/transactions/rows?page=-5')
    assert r.status_code == 200
