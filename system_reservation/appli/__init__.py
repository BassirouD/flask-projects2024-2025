import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from appli.auth import auth
from appli.reservation import service
from flask_jwt_extended import JWTManager

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key'),
                            SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                                                   'sqlite:///reservations.db'),
                            SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    from .models import User, Service, Reservation, Calendar

    create_db(app)
    JWTManager(app)

    # Looking to send emails in production? Check out our Email API/SMTP product!
    app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
    app.config['MAIL_PORT'] = 2525
    app.config['MAIL_USERNAME'] = '4397c5ab6ef133'
    app.config['MAIL_PASSWORD'] = '5de540e7e7a57d'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    app.register_blueprint(auth)
    app.register_blueprint(service)

    return app


def create_db(app):
    if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI']):
        with app.app_context():
            db.create_all()

    with app.app_context():
        from .models import User

        user = User.query.filter_by(email='admin@koula.com').first()
        if user is None:
            user = User(email='admin@koula.com', username='admin')
            user.set_password('adminpassword')
            db.session.add(user)
            db.session.commit()
