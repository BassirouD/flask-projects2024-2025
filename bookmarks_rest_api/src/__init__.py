from flask import Flask, jsonify, redirect
from os import path
import os
from src.auth import auth
from src.bookmarks import bookmarks
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.models import db, Bookmark
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
from src.configs.swagger import template, swagger_config

DB_NAME = 'database.db'


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
                                SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                                                       'sqlite:///bookmarks.db'),
                                SQLALCHEMY_TRACK_MODIFICATIONS=False,
                                JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'JWT_SECRET_KEY'),
                                Swagger={
                                    'title': 'Bookmarks REST API',
                                    'uiversion': 3,
                                }
                                )
    else:
        app.config.from_mapping(test_config)

    db.init_app(app)
    from .models import User, Bookmark
    create_db(app)

    JWTManager(app)

    app.register_blueprint(bookmarks)
    app.register_blueprint(auth)

    Swagger(app, config=swagger_config, template=template)

    @app.route('/<short_url>')
    @swag_from('../docs/short_url.yml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()
        if bookmark:
            bookmark.visited = bookmark.visited + 1
            db.session.commit()
            return redirect(bookmark.url)

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def not_found(error):
        return jsonify({'error': str(error)}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def internal_error(error):
        return jsonify({'error': str(error)}), HTTP_500_INTERNAL_SERVER_ERROR

    return app


def create_db(app):
    if not path.exists('src/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Database created')
