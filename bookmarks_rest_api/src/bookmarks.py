from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity

from .models import Bookmark, db

from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, HTTP_200_OK, \
    HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from flasgger import swag_from

bookmarks = Blueprint('bookmarks', __name__, url_prefix='/api/v1/bookmarks')


@bookmarks.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()
    if request.method == 'POST':
        body = request.get_json().get('body')
        url = request.get_json().get('url')

        if not validators.url(url):
            return jsonify({'error': 'Invalid URL'}), HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return jsonify({'error': 'Bookmark already exists'}), HTTP_409_CONFLICT

        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            'id': bookmark.id,
            'url': bookmark.url,
            'short_url': bookmark.short_url,
            'visit': bookmark.visited,
            'created_at': bookmark.created_at,
            'updated_at': bookmark.updated_at,
        }), HTTP_201_CREATED

    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        bookmark_list = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        data = []
        for bookmark in bookmark_list:
            data.append({
                'id': bookmark.id,
                'url': bookmark.url,
                'short_url': bookmark.short_url,
                'visit': bookmark.visited,
                'created_at': bookmark.created_at,
                'updated_at': bookmark.updated_at,
                'body': bookmark.body,
            })
        meta = {
            'pages': bookmark_list.pages,
            'page': bookmark_list.page,
            'total_count': bookmark_list.total,
            'prev': bookmark_list.prev_num,
            'next': bookmark_list.next_num,
            'has_prev': bookmark_list.has_prev,
            'has_next': bookmark_list.has_next,
        }
        return jsonify({'data': data, 'meta': meta}), HTTP_200_OK


@bookmarks.get('/<int:id>')
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()
    if not bookmark:
        return jsonify({'error': 'Bookmark not found'}), HTTP_404_NOT_FOUND
    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visit': bookmark.visited,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at,
        'body': bookmark.body,
    })


@bookmarks.put('/<int:id>')
@jwt_required()
def update_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()
    if not bookmark:
        return jsonify({'error': 'Bookmark not found'}), HTTP_404_NOT_FOUND

    body = request.get_json().get('body')
    url = request.get_json().get('url')

    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), HTTP_400_BAD_REQUEST

    bookmark.body = body
    bookmark.url = url
    db.session.commit()
    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visit': bookmark.visited,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at,
    }), HTTP_200_OK


@bookmarks.delete('/<int:id>')
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(id=id, user_id=current_user).first()
    if not bookmark:
        return jsonify({'error': 'Bookmark not found'}), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({}), HTTP_204_NO_CONTENT


@bookmarks.get('/stats')
@jwt_required()
@swag_from('../docs/bookmarks/stats.yml')
def get_stats():
    current_user = get_jwt_identity()
    data = []
    items = Bookmark.query.filter_by(user_id=current_user).all()

    for bookmark in items:
        new_link = {
            'visited': bookmark.visited,
            'url': bookmark.url,
            'id': bookmark.id,
            'short_url': bookmark.short_url,
        }
        data.append(new_link)

    return jsonify({'data': data}), HTTP_200_OK