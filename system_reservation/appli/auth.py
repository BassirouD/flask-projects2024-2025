from flask import Blueprint
from flask_restful import reqparse

from appli.services.auth_services import AuthServices

auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

user_register = reqparse.RequestParser()
user_login = reqparse.RequestParser()

user_register.add_argument('username', type=str, required=True, help='Name cannot be empty')
user_register.add_argument('email', type=str, required=True, help='Email cannot be empty')
user_register.add_argument('password', type=str, required=True, help='Password cannot be empty')
user_register.add_argument('password2', type=str, required=True, help='Password cannot be empty')

user_login.add_argument('email', type=str, required=True, help='Email cannot be empty')
user_login.add_argument('password', type=str, required=True, help='Password cannot be empty')


@auth.route('/register', methods=['POST'])
def register():
    args = user_register.parse_args()
    username = args['username']
    password = args['password']
    password2 = args['password2']
    email = args['email']

    return AuthServices.register_user(username=username, password=password, email=email, password2=password2)



@auth.route('/login', methods=['POST'])
def login():
    args = user_login.parse_args()
    email = args['email']
    password = args['password']
    return AuthServices.login_user(email, password)