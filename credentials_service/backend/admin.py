from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from utils import load_teams_data, save_teams_data, get_current_user, config_file_lock
import time

admin_blueprint = Blueprint('admin', __name__)

pin_digits = 6

@admin_blueprint.route('/login', methods=['POST'])
def admin_login():
    time.sleep(1.5) # Avoid brute force attacks
    data = request.get_json()
    token = data.get('token')

    if token == load_teams_data()['gameserver_token']:
        access_token = create_access_token(identity={'is_admin': True})
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Invalid credentials"}), 401

@admin_blueprint.route('/teams', methods=['GET'])
@jwt_required()
def get_teams():
    current_user = get_current_user()
    if not current_user.get('is_admin', False):
        return jsonify({"msg": "Forbidden: Admin access required"}), 403
    
    teams_data = load_teams_data()

    return jsonify([{
        "id": team['id'],
        "name": team['name'],
        "pins": team['pins'],
        "token":team['token'],
        "wireguard_port":team['wireguard_port'],
        "nop":team['nop'],
    } for team in teams_data['teams'] if not team['nop']]), 200
