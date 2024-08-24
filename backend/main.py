from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import datetime
from datetime import timezone
from hashlib import sha256
import jwt


app = Flask(__name__)
CORS(app)  

DATA_FILE = 'trade_attributes.json'
LOG_FILE = 'activity_log.json'

PASSWORD = sha256(b'sudip').hexdigest()
JWT_SECRET = 'secret'

def read_json_file():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def read_activity_log():
    DATE = datetime.datetime.now().strftime("%Y-%d-%m")
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
        
    if DATE in data:
        return {DATE: data[DATE]}
    else:
        return {}

def write_json_file(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def verify_token(token):
    try:
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'],options={"verify_exp": True})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


@app.route('/api/read', methods=['GET'])
def read():
    data = read_json_file()
    return jsonify(data)


@app.route('/api/login',methods=['POST'])
def login():
    password = request.json['password']
    token = jwt.encode(
        {'password': password, 
         'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)}, 
         JWT_SECRET, 
         algorithm='HS256')
    if password == PASSWORD:
        return jsonify({"success":True,'token':token})
    else:
        return jsonify({"success":False})

@app.route('/api/log', methods=['GET'])
def read_log():
    data = read_activity_log()
    return jsonify(data)

@app.route('/api/write', methods=['POST'])
def write():
    token = request.headers.get('Authorization')
    if not verify_token(token):
        return jsonify({"success":False,"message": "Invalid token"}), 401
    data = request.json['data']
    write_json_file(data)
    return jsonify({"success":True,"message": "Data written successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
