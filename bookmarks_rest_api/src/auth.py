from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from .models import User, db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_401_UNAUTHORIZED, HTTP_200_OK
from flasgger import swag_from

auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth.post('/register')
@swag_from('../docs/auth/register.yml')
def register():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), HTTP_400_BAD_REQUEST

    if not username.isalnum():
        return jsonify({'error': 'Username must be alphanumeric'}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error': 'Email is not valid'}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered'}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already registered'}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)
    user = User(username=username, email=email, password=pwd_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'username': username,
            'email': email,
        }
    }), HTTP_201_CREATED


@auth.post('/login')
@swag_from('../docs/auth/login.yml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({'user': {
            'refresh_token': refresh_token,
            'access_token': access_token,
            'email': user.email,
            'username': user.username,
        }}), HTTP_200_OK

    return jsonify({'error': 'Email or password is incorrect'}), HTTP_401_UNAUTHORIZED


@auth.get('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        'username': user.username,
        'email': user.email,
    }), HTTP_200_OK


@auth.get('/token/refresh')
@jwt_required(refresh=True)
def token_refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({
        'access_token': access_token,
    }), HTTP_200_OK
