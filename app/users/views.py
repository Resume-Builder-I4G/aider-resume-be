import jwt
from flask import current_app as app, request, render_template
from . import users_bp, token_required
from app import db
from app.email import send_mail
from app.models import User

@users_bp.route('/', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if 'email' not in data or 'password' not in data or 'name' not in data:
            return {
                'error': 'Invalid Data',
                'message': 'Name, email and password must be present.'
            }, 400
        if len(data['name']) < 5 or len(data['email']) < 8 or len(data['password']) < 8:
            return {
                'error': 'Invalid Data',
                'message': 'Name must be ateast 5 characters, email must be'
                    'atleast 8 characters and password must be atleast 8 characters'
            }, 400
        u = User.query.filter_by(email=data['email']).first()
        if u:
            return {
                'error': 'Invalid Data',
                'message': 'Email already exist'
            }, 400
        u = User(name=data['name'], email=data['email'])
        u.set_password(data['password'])
        db.session.add(u)
        db.session.commit()
        # try:
        #     send_mail(
        #         [u.email], 'Welcome to Aider', 
        #         'mail/welcome', u=u
        #     )
        # except Exception as e:
        #     return {
        #         'error': 'Something went wrong',
        #         'message': str(e)
        #     }, 500
        return u.to_dict(), 201
    except Exception as e:
        return {
            'error': 'Bad data',
            'message': str(e)
        }, 400

@users_bp.route('/tokens/', methods=['POST'])
def get_token():
    try:
        data = request.get_json()

        if 'email' not in data or 'password' not in data:
            return {
                'error': 'Invalid data',
                'message': 'email and password must be present.'
            }, 400
        u = User.query.filter_by(email=data['email']).first()
        if not u or not u.check_password(data['password']):
            return {
                'error': 'Invalid Data',
                'message': 'invalid email or password'
            }, 400
        try:
            token = jwt.encode(
                {'user_id': str(u.id)},
                app.config['SECRET_KEY']
            )
            return {
                'token': token
            }, 200
        except Exception as e:
            return {
                'error': 'Sonething went wrong',
                'message': str(e)
            }, 500
    except Exception as e:
        return {
            'error': 'Bad data',
            'message': str(e)
        }, 400 

@users_bp.route('/', methods=['PUT'])
@token_required
def update_user(current_user: User):
    try:
        data = request.get_json()
        if 'name' not in data:
            return {
                'error': 'Invalid Data',
                'message': 'Name is not present'
            }, 400
        current_user.name=data['name']
        db.session.commit()
        return {
            'success': 'Data updated successfully'
        }, 200
    except Exception as e:
        return {
            'error': 'Bad data',
            'message': str(e)
        }, 400

@users_bp.route('/')
@token_required
def get_user(current_user):
    return current_user.to_dict()

@users_bp.route('/confirm/')
@token_required
def confirm_account(current_user: User):
    current_user.is_confirmed = True
    db.session.commit()
    return '', 204

@users_bp.route('/get_password_reset_token/', methods=['POST'])
def get_password_reset_token():
    if request.headers.get('Authorization'):
        return {
            'error': 'Forbidden'
        }, 403
    data = request.get_json()
    u:User=User.query.filter_by(email=data['email']).first()
    print(u)
    if u:
        token = u.get_reset_token()
        # send_mail(
        #     [u.email], 'Reset Your Password', 
        #     'mail/reset_password', token=token, u=u
        # )

        return {
            'url': request.host_url+'api/v2/users/reset_password/'+token
        }

@users_bp.route('/reset_password/<token>/', methods=['POST'])
def reset_password(token):
    if request.headers.get('Authorization'):
        return {
            'error': 'Forbidden'
        }, 403
    data = request.get_json()
    if 'password' not in data or 'confirm password' not in \
            data or data['password'] !=data['confirm password'] or len(data['password'] < 8):
        return {
            'error': 'Password and confirm password must be given and must be equal and should be at'
        }, 400
    user = User.verify_reset_token(token)
    if user is not None:
        user.set_password(request.get_json()['password'])
        db.session.commit()
    return {
        'success': 'Data updated successfully'
    }