from unittest.mock import patch


def test_unauthenticated_request_redirects_to_login(app):
    with app.test_client() as c:
        r = c.get('/admin/')
        assert r.status_code == 302
        assert '/admin/login' in r.headers['Location']


def test_unauthenticated_items_redirects(app):
    with app.test_client() as c:
        r = c.get('/admin/items')
        assert r.status_code == 302


def test_login_page_renders(app):
    with app.test_client() as c:
        r = c.get('/admin/login')
        assert r.status_code == 200


def test_login_empty_username_flashes_error(app):
    with app.test_client() as c:
        r = c.post('/admin/login', data={'username': '', 'password': 'secret'})
        assert r.status_code == 200


def test_login_empty_password_flashes_error(app):
    with app.test_client() as c:
        r = c.post('/admin/login', data={'username': 'admin', 'password': ''})
        assert r.status_code == 200


def test_login_success_redirects_to_dashboard(app):
    with app.test_client() as c:
        with patch('ptl_buddy_server.admin.auth.ldap_check_admin', return_value=True) as mock_ldap:
            r = c.post('/admin/login', data={'username': 'admin', 'password': 'secret'})
            mock_ldap.assert_called_once_with('admin', 'secret')
            assert r.status_code == 302
            assert '/admin/' in r.headers['Location']


def test_login_bad_credentials_stays_on_login(app):
    with app.test_client() as c:
        with patch('ptl_buddy_server.admin.auth.ldap_check_admin', return_value=False):
            r = c.post('/admin/login', data={'username': 'admin', 'password': 'wrong'})
            assert r.status_code == 200


def test_already_logged_in_redirects_from_login(app):
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['admin_user'] = 'admin'
        r = c.get('/admin/login')
        assert r.status_code == 302
        assert '/admin/' in r.headers['Location']


def test_logout_clears_session_and_redirects(client):
    r = client.get('/admin/logout')
    assert r.status_code == 302
    assert '/admin/login' in r.headers['Location']


def test_logout_then_protected_route_redirects(client):
    client.get('/admin/logout')
    r = client.get('/admin/')
    assert r.status_code == 302
    assert '/admin/login' in r.headers['Location']
