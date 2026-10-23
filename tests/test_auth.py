import pytest
from app import create_app, db
from app.auth.models import User


@pytest.fixture
def app():
    application = create_app('testing')
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(username='testadmin', email='admin@test.com', role='admin', is_active=True)
        user.set_password('Admin@123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(app):
    with app.app_context():
        user = User(username='testuser', email='user@test.com', role='user', is_active=True)
        user.set_password('User@123')
        db.session.add(user)
        db.session.commit()
        return user


def test_register_new_user(client):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@test.com',
        'city': 'Boston',
        'password': 'NewPass@1',
        'confirm_password': 'NewPass@1',
        'csrf_token': 'test'
    }, follow_redirects=False)
    assert response.status_code in (200, 302)


def test_register_duplicate_email(client, regular_user):
    response = client.post('/auth/register', data={
        'username': 'another',
        'email': 'user@test.com',
        'city': 'NYC',
        'password': 'Another@1',
        'confirm_password': 'Another@1',
        'csrf_token': 'test'
    })
    assert b'already registered' in response.data


def test_login_valid_user(client, regular_user):
    response = client.post('/auth/login', data={
        'email': 'user@test.com',
        'password': 'User@123',
        'csrf_token': 'test'
    }, follow_redirects=False)
    assert response.status_code in (200, 302)


def test_login_invalid_password(client, regular_user):
    response = client.post('/auth/login', data={
        'email': 'user@test.com',
        'password': 'WrongPassword1',
        'csrf_token': 'test'
    })
    assert b'Invalid credentials' in response.data or response.status_code == 200


def test_user_password_hashing(app):
    with app.app_context():
        user = User(username='hashtest', email='hash@test.com')
        user.set_password('TestPass@1')
        assert user.check_password('TestPass@1')
        assert not user.check_password('WrongPass@1')


def test_user_is_admin(app):
    with app.app_context():
        admin = User(username='admin2', email='admin2@test.com', role='admin')
        admin.set_password('Admin@123')
        regular = User(username='regular', email='regular@test.com', role='user')
        regular.set_password('User@123')
        assert admin.is_admin()
        assert not regular.is_admin()


def test_user_to_dict(app):
    with app.app_context():
        user = User(username='dicttest', email='dict@test.com', role='user', city='NYC')
        user.set_password('Pass@1234')
        db.session.add(user)
        db.session.commit()
        d = user.to_dict()
        assert d['username'] == 'dicttest'
        assert d['email'] == 'dict@test.com'
        assert d['role'] == 'user'
        assert 'password_hash' not in d


def test_logout_redirects(client):
    response = client.get('/auth/logout', follow_redirects=False)
    assert response.status_code == 302
