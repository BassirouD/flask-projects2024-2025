from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import reqparse, fields, marshal_with
from appli.services.reservation_services import ReservationService

service = Blueprint('service', __name__, url_prefix='/api/v1/services')

service_parse = reqparse.RequestParser()
reservation_parse = reqparse.RequestParser()
reservation_update = reqparse.RequestParser()
calendar_parse = reqparse.RequestParser()

service_parse.add_argument('name', type=str, required=True, help='Name cannot be empty')
service_parse.add_argument('description', type=str, required=False)
service_parse.add_argument('duration', type=int, required=False, help='Duration cannot be empty')
service_parse.add_argument('price', type=float, required=False, help='Price cannot be empty')

reservation_parse.add_argument('reservation_date', type=str, required=True,
                               help='Reservation date cannot be empty')
reservation_parse.add_argument('start_time', type=str, required=True,
                               help='Start time cannot be empty')
reservation_parse.add_argument('user_id', type=int, required=True)
reservation_parse.add_argument('service_id', type=int, required=True)

reservation_update.add_argument('new_date', type=str, required=True, )
reservation_update.add_argument('new_time', type=str, required=True, )

calendar_parse.add_argument('date', type=str, required=True, help='Date cannot be empty')
calendar_parse.add_argument('available_hours', type=str, required=True, help='Available hours cannot be empty')
calendar_parse.add_argument('service_id', type=int, required=True, help='Service id cannot be empty')

service_fields = {
    'name': fields.String,
    'description': fields.String,
    'duration': fields.Integer,
    'price': fields.Float
}


@service.route('/')
@jwt_required()
@marshal_with(service_fields)
def get_services():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    return ReservationService.get_all_service()


@service.route('/', methods=['POST'])
@jwt_required()
def add_service():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    args = service_parse.parse_args()
    name = args['name']
    description = args['description']
    duration = args['duration']
    price = args['price']
    return ReservationService.add_service(name, description, duration, price)


@service.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def remove_service(id):
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    return ReservationService.delete_service(id)


@service.route('/<int:id>', methods=['PATCH'])
@jwt_required()
def update_service(id):
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    args = service_parse.parse_args()
    name = args['name']
    description = args['description']
    duration = args['duration']
    price = args['price']
    return ReservationService.update_service(id=id, name=name, description=description, duration=duration, price=price)


@service.route('/calendars', methods=['POST'])
@jwt_required()
def add_calendar():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Access denied. Admins only.'}), 403

    args = calendar_parse.parse_args()
    service_id = args['service_id']
    date = args['date']
    available_hours = args['available_hours']
    return ReservationService.add_calendar(service_id, date, available_hours)


@service.route('/reservations', methods=['POST'])
@jwt_required()
def do_reservation():
    args = reservation_parse.parse_args()
    reservation_date = args['reservation_date']
    start_time = args['start_time']
    user_id = args['user_id']
    service_id = args['service_id']
    return ReservationService.do_reservation(user_id, service_id, reservation_date, start_time)


@service.route('/reservations/upcoming', methods=['GET'])
@jwt_required()
def upcoming_reservations():
    current_user = get_jwt_identity()
    return ReservationService.get_upcoming_reservation(current_user['id'])


@service.route('/reservations/past', methods=['GET'])
@jwt_required()
def past_reservations():
    current_user = get_jwt_identity()
    return ReservationService.get_pass_reservation(current_user['id'])


@service.route('/reservations/<int:reservation_id>/cancel', methods=['PATCH'])
@jwt_required()
def cancel_reservation(reservation_id):
    current_user = get_jwt_identity()
    user_id = current_user['id']
    return ReservationService.cancel_reservation(user_id, reservation_id)


@service.route('/reservations/<int:reservation_id>/modify', methods=['PATCH'])
@jwt_required()
def update_reservation(reservation_id):
    args = reservation_update.parse_args()
    new_date = args['new_date']
    new_time = args['new_time']
    return ReservationService.modify_reservation(reservation_id, new_date, new_time)
