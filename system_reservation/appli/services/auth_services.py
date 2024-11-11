from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token


class AuthServices:
    @staticmethod
    def register_user(username, email, password, password2):
        from appli.models import User
        from appli import db

        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if not username.isalnum():
            return jsonify({'error': 'Username must be alphanumeric'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'User already exists'}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 409
        if password2 != password:
            return jsonify({'error': 'Passwords do not match'}), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully',
                        'user': {
                            'username': user.username,
                            'email': user.email
                        }}), 201

    @staticmethod
    def login_user(email, password):
        from appli.models import User
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity={'id': user.id, 'role': user.role})
            refresh_token = create_refresh_token(identity=user.id)
            return jsonify({
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            })
        return jsonify({'error': 'Invalid credentials'}), 401
