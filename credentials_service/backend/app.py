from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from utils import load_teams_data, prepare_json_file, BASE_DIR, DEBUG
import os, subprocess
from admin import admin_blueprint
from user import user_blueprint
from werkzeug.security import safe_join

load_dotenv()

frontend_folder = os.path.join(BASE_DIR, "frontend") if not DEBUG else os.path.join(BASE_DIR, "../frontend/dist")

app = Flask(__name__)

secret_token = load_teams_data()['gameserver_token']

app.config['SECRET_KEY'] = secret_token
app.config['JWT_SECRET_KEY'] = secret_token
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False


jwt = JWTManager(app)

@app.after_request
def handle_options(response):
    if DEBUG:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With, Authorization"
    return response

app.register_blueprint(admin_blueprint, url_prefix='/api/admin')
app.register_blueprint(user_blueprint, url_prefix='/api/user')

@app.route('/')
def index():
    return send_from_directory(frontend_folder, "index.html")

@app.route('/<path:path>')
def catch_all(path):
    final_path = safe_join(frontend_folder, path)
    if os.path.exists(final_path):
        return send_from_directory(frontend_folder, path)
    else:
        return send_from_directory(frontend_folder, "index.html")

if __name__ == "__main__":
    prepare_json_file()
    try:
        if DEBUG:
            app.run(host='0.0.0.0', port=4040, debug=True)
        else:
            os.chdir(BASE_DIR)
            subprocess.Popen(["gunicorn", "--workers", "4", "--reuse-port", "--bind", "0.0.0.0:4040", "app:app"]).wait()
    except KeyboardInterrupt:
        pass
        
