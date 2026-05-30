from flask import Blueprint, request, jsonify
from flask_mail import Message
from app import mail

mail_bp = Blueprint('mail', __name__, url_prefix='/api')

@mail_bp.route('/contact', methods=['POST'])
def contact():
    data    = request.get_json()
    name    = data.get('name', '').strip()
    email   = data.get('email', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'error': 'All fields required'}), 400

    try:
        msg = Message(
            subject    = f'New Contact from {name} — 9janetmovies',
            recipients = ['9janetmovies@9janetmovies.com.ng'],
            body       = f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}'
        )
        mail.send(msg)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500