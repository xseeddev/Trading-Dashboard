from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import datetime
from datetime import timezone
from hashlib import sha256
import jwt
from authentication import portal_login, check_user_login
from logger import setup_logger


app = Flask(__name__)
CORS(app)  
logger = setup_logger("Main App Logger")

# Load configuration from app_config.json
with open('app_config.json', 'r') as config_file:
    config = json.load(config_file)

DATA_FILE = config.get('DATA_FILE', 'trade_attributes.json')
LOG_FILE = config.get('LOG_FILE', 'activity_log.json')

PASSWORD = sha256(b'sudip').hexdigest()
JWT_SECRET = 'secret'

def read_activity_log(): # To Fix
    DATE = datetime.datetime.now().strftime("%Y-%d-%m")
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
        
    if DATE in data:
        return {DATE: data[DATE]}
    else:
        return {}

@app.route('/api/login',methods=['POST'])
def login():
    portal_login()

@app.route('/api/log', methods=['GET'])
def read_log():
    data = read_activity_log()# Fix Function
    return jsonify(data)

@app.route('/api/read', methods=['GET'])# Fix and remove
def read():
    data = read_json_file()
    return jsonify(data)

@app.route('/api/checkToken', methods=['POST'])
def checkToken():
    return check_user_login()

@app.route('/api/exec', methods=['POST'])
def execute_operation():
    return None
    # inputparams = [{
    #     "auth_token": token, portal auth token
    #     "user_id": user_id,
    #     "password": password,
    #     "api_key": api_key,
    #     "secret_key": secret_key,
    #     "name": client
    #     "Trade_attributes":trade_att        
    # }]

    # Check auth token
    # get trade attributes
    # execute trade

    # return "Status"

if __name__ == '__main__':
    app.run(debug=True)
