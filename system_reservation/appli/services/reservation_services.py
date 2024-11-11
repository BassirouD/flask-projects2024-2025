from datetime import datetime, time
from appli.utils import send_confirmation_email
from flask import jsonify


class ReservationService:
    @staticmethod
    def get_all_service():
        from appli.models import Service
        service_list = Service.query.all()
        return service_list

    @staticmethod
    def add_service(name, description, duration, price):
        from appli.models import Service
        from appli import db
        if len(name) < 2:
            return jsonify({'message': 'Name must be at least 2 characters.'}), 400
        if duration < 0:
            return jsonify({'message': 'Duration must be positive.'}), 400
        if price < 0:
            return jsonify({'message': 'Price must be positive.'}), 400

        service = Service(name=name, description=description, duration=duration, price=price)
        db.session.add(service)
        db.session.commit()
        return jsonify({'message': 'Service added successfully',
                        'service': {
                            'name': name,
                            'description': description,
                            'duration': duration,
                            'price': price
                        }}), 201

    @staticmethod
    def delete_service(id):
        from appli.models import Service
        from appli import db

        service = Service.query.filter_by(id=id).first()
        if not service:
            return jsonify({'message': 'Service not found.'}), 404
        db.session.delete(service)
        db.session.commit()
        return jsonify({'message': 'Service deleted successfully'}), 204

    @staticmethod
    def update_service(id, name, description, duration, price):
        from appli.models import Service
        from appli import db
        service = Service.query.filter_by(id=id).first()
        if not service:
            return jsonify({'message': 'Service not found.'}), 404
        service.name = name
        service.description = description
        service.duration = duration
        service.price = price
        db.session.commit()
        return jsonify({'message': 'Service edited successfully'}), 200

    @staticmethod
    def get_service(id):
        from appli.models import Service
        service = Service.query.filter_by(id=id).first()
        if not service:
            return jsonify({'message': 'Service not found.'}), 404
        return service

    @staticmethod
    def do_reservation(user_id, service_id, reservation_date, start_time):
        from appli.models import Reservation, User, Service, Calendar
        from appli import db
        from datetime import datetime

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User not found.'}), 404
        service = Service.query.filter_by(id=service_id).first()
        if not service:
            return jsonify({'message': 'Service not found.'}), 404

        # Vérifier la disponibilité dans le calendrier
        calendar_entry = Calendar.query.filter_by(service_id=service_id, date=reservation_date).first()
        if not calendar_entry:
            return jsonify({'message': 'No available slots for this date'}), 404

        # Vérifier que le créneau horaire est disponible
        available_hours = calendar_entry.available_hours.split(", ")
        if start_time not in available_hours:
            return jsonify({'message': f"Time slot {start_time} not available"}), 400

        # Retirer le créneau réservé du calendrier
        try:
            available_hours.remove(start_time)
        except ValueError:
            return jsonify({"message": f"Error: Time slot {start_time} is not in the available list"}), 400

        calendar_entry.available_hours = ", ".join(available_hours)
        db.session.commit()

        # Combiner la date et l'heure pour créer un objet datetime
        reservation_datetime = datetime.combine(datetime.strptime(reservation_date, '%Y-%m-%d'), datetime.min.time())

        new_reservation = Reservation(
            user_id=user.id,
            service_id=service.id,
            reservation_date=reservation_datetime,  # Utiliser datetime ici
            start_time=datetime.strptime(start_time, "%H:%M").time(),
        )

        db.session.add(new_reservation)
        db.session.commit()

        send_confirmation_email(user, service.name, reservation_date, start_time)

        return jsonify({
            'message': 'Reservation created successfully',
            'reservation': {
                'id': new_reservation.id,
                'service': service.name,
                'reservation_date': new_reservation.reservation_date.strftime('%Y-%m-%d'),  # Affichage formaté
                'start_time': new_reservation.start_time.strftime('%H:%M'),
                'status': new_reservation.status
            }
        })

    @staticmethod
    def add_calendar(service_id, date, available_hours):
        from appli.models import Service, Calendar
        from appli import db
        service = Service.query.filter_by(id=service_id).first()
        if not service:
            return jsonify({'message': 'Service not found.'}), 404

        # Obtenir la date et vérifier qu'elle est au bon format
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "Invalid date format, should be YYYY-MM-DD"}), 400
        if not available_hours:
            return jsonify({"message": "Available hours not provided"}), 400

        # Vérifier s'il existe déjà une entrée pour ce service et cette date
        existing_calendar = Calendar.query.filter_by(service_id=service_id, date=date).first()
        if existing_calendar:
            return jsonify({"message": "Calendar already exists for this date"}), 400

            # Créer une nouvelle entrée de calendrier
        new_calendar = Calendar(
            date=date,
            available_hours=available_hours,  # Doit être sous la forme '10:00, 12:00, 14:00'
            service_id=service.id
        )

        # Ajouter l'entrée dans la base de données
        db.session.add(new_calendar)
        db.session.commit()
        return jsonify({
            'message': 'Calendar added successfully',
            'calendar': {
                'id': new_calendar.id,
                'date': new_calendar.date.strftime('%Y-%m-%d'),
                'available_hours': new_calendar.available_hours,
                'service': service.name
            }
        })

    @staticmethod
    def get_pass_reservation(user_id):
        from appli.models import Reservation
        pass_reservation = Reservation.query.filter(Reservation.user_id == user_id,
                                                    Reservation.reservation_date < datetime.now().date()).all()
        if not pass_reservation:
            return jsonify({'message': 'No past reservations found.'}), 404

        reservations_list = []
        for reservation in pass_reservation:
            reservations_list.append({
                'id': reservation.id,
                'service': reservation.service.name,
                'reservation_date': reservation.reservation_date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'status': reservation.status
            })

        return jsonify({'past_reservations': reservations_list})

    @staticmethod
    def get_upcoming_reservation(user_id):
        from appli.models import Reservation
        upcoming_reservation = Reservation.query.filter(Reservation.user_id == user_id,
                                                        Reservation.reservation_date >= datetime.now().date()).all()
        if not upcoming_reservation:
            return jsonify({'message': 'No upcoming reservations found.'}), 404

        upcoming_reservations_list = []
        for reservation in upcoming_reservation:
            upcoming_reservations_list.append({
                'id': reservation.id,
                'service': reservation.service.name,
                'reservation_date': reservation.reservation_date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'status': reservation.status
            })

        return jsonify({'upcoming_reservations': upcoming_reservations_list})

    @staticmethod
    def cancel_reservation(user_id, reservation_id):
        from appli.models import Reservation, Calendar
        from appli import db
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()
        if not reservation:
            return jsonify({'message': 'No reservation found.'}), 404

        if reservation.status == 'cancelled':
            return jsonify({'message': 'Reservation is already cancelled.'}), 400

        if reservation.reservation_date.date() < datetime.now().date():
            return jsonify({'message': 'Cannot cancel past reservations.'}), 400

        reservation.status = 'cancelled'
        reservation_date_only = reservation.reservation_date.date()

        # Si vous souhaitez aussi restaurer l'horaire annulé dans le calendrier
        calendar_entry = Calendar.query.filter_by(
            service_id=reservation.service_id,
            date=reservation_date_only
        ).first()

        if calendar_entry:
            available_hours = calendar_entry.available_hours.split(", ")
            available_hours.append(reservation.start_time.strftime('%H:%M'))
            calendar_entry.available_hours = ", ".join(sorted(available_hours))  # Trier les créneaux horaires

        db.session.commit()
        return jsonify({'message': 'Reservation cancelled successfully'}), 200

    @staticmethod
    def modify_reservation(reservation_id, n_date, n_time):
        from appli.models import Reservation, Calendar
        from appli import db
        from datetime import datetime

        # Convertir les dates et heures
        try:
            new_date = datetime.strptime(n_date, '%Y-%m-%d').date()
            new_time = datetime.strptime(n_time, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid date or time format. Should be YYYY-MM-DD and HH:MM.'}), 400

        reservation = Reservation.query.filter_by(id=reservation_id).first()
        if not reservation:
            return jsonify({'message': 'No reservation found.'}), 404
        if reservation.status == 'cancelled':
            return jsonify({'message': 'Cannot modify a cancelled reservation.'}), 400
        if reservation.reservation_date.date() < datetime.now().date():
            return jsonify({'message': 'Cannot modify past reservations.'}), 400

        # Rechercher l'entrée dans le calendrier pour l'ancienne réservation
        calendar_entry = Calendar.query.filter_by(service_id=reservation.service_id,
                                                  date=reservation.reservation_date.date()).first()
        if not calendar_entry:
            return jsonify({'error': 'No calendar entry found for the current reservation'}), 404

        # Rechercher le créneau horaire disponible pour la nouvelle date
        new_datetime = datetime.combine(new_date, time(0, 0, 0, 0))
        print(new_datetime)
        new_calendar_entry = Calendar.query.filter_by(service_id=reservation.service_id, date=new_datetime).first()
        if not new_calendar_entry:
            return jsonify({'error': 'No available slots for this date'}), 404

        # Vérifier si le nouveau créneau horaire est disponible
        new_available_hours = new_calendar_entry.available_hours.split(", ")
        if new_time.strftime('%H:%M') not in new_available_hours:
            return jsonify({'error': f"Time slot {new_time.strftime('%H:%M')} not available"}), 400

        # Rendre l'ancien créneau disponible (on ne fait cela qu'après avoir validé la disponibilité du nouveau créneau)
        available_hours = calendar_entry.available_hours.split(", ")
        available_hours.append(reservation.start_time.strftime("%H:%M"))
        calendar_entry.available_hours = ", ".join(sorted(available_hours))

        # Retirer le nouveau créneau du calendrier
        new_available_hours.remove(new_time.strftime('%H:%M'))
        new_calendar_entry.available_hours = ", ".join(sorted(new_available_hours))  # Trier les créneaux horaires

        # Modifier la réservation
        reservation.reservation_date = new_date
        reservation.start_time = new_time

        # Appliquer tous les changements dans une seule transaction
        db.session.commit()

        return jsonify({
            'message': 'Reservation updated successfully',
            'reservation': {
                'id': reservation.id,
                'new_date': reservation.reservation_date.strftime('%Y-%m-%d'),
                'new_time': reservation.start_time.strftime('%H:%M')
            }
        })




