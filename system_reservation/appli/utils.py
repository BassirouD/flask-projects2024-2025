def send_confirmation_email(user, service_name, reservation_date, start_time):
    from app import mail
    from flask_mail import Message

    # Créer le message de confirmation
    msg = Message(
        subject='Confirmation de réservation',
        sender='noreply@reseravation_koula.com',
        recipients=[user.email],  # Email du destinataire
        body=f"Bonjour Mr. {user.username},\n\nVotre réservation pour le service '{service_name}' "
             f"le {reservation_date} à {start_time} "
             f"a été confirmée.\n\nMerci pour votre confiance."
    )

    # Envoyer l'email
    try:
        mail.send(msg)
        print("Email de confirmation envoyé avec succès")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {str(e)}")
