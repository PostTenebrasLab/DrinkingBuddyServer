import logging
import os

from flask import flash, redirect, render_template, request, session, url_for

from .blueprint import admin_bp

log = logging.getLogger(__name__)

_ldap_url               = os.environ.get('LDAP_URL',               'ldap://localhost')
_ldap_user_search_base  = os.environ.get('LDAP_USER_SEARCH_BASE',  'ou=users,dc=example,dc=org')
_ldap_group_search_base = os.environ.get('LDAP_GROUP_SEARCH_BASE', 'ou=groups,dc=example,dc=org')
ADMIN_GROUP = 'admins'


def ldap_check_admin(username, password):
    """Authenticate user via LDAP and verify admin group membership."""
    import ldap3

    user_dn = f'uid={username},{_ldap_user_search_base}'
    log.debug('LDAP connecting to %s', _ldap_url)
    log.debug('LDAP binding as %s', user_dn)

    try:
        server = ldap3.Server(_ldap_url, get_info=ldap3.NONE)
        conn = ldap3.Connection(server, user=user_dn, password=password)
        if not conn.bind():
            log.warning('LDAP bind failed for %s: %s', user_dn, conn.result)
            return False
        log.debug('LDAP bind successful for %s', user_dn)

        # Try groupOfNames style (FreeIPA)
        f1 = f'(&(objectClass=groupOfNames)(cn={ADMIN_GROUP})(member={user_dn}))'
        conn.search(_ldap_group_search_base, f1)
        if conn.entries:
            return True

        # Try posixGroup style
        f2 = f'(&(objectClass=posixGroup)(cn={ADMIN_GROUP})(memberUid={username}))'
        conn.search(_ldap_group_search_base, f2)
        if conn.entries:
            return True

        log.warning('User %s authenticated but is not in group "%s"', username, ADMIN_GROUP)
        return False

    except Exception as e:
        log.error('LDAP error: %s', e, exc_info=True)
        return False


@admin_bp.before_request
def require_login():
    if request.endpoint in ('admin.login', 'admin.logout'):
        return
    if 'admin_user' not in session:
        return redirect(url_for('admin.login'))


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_user' in session:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password required.', 'error')
        elif ldap_check_admin(username, password):
            session['admin_user'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials or not in the admin group.', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_user', None)
    return redirect(url_for('admin.login'))
