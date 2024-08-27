import datetime
from datetime import timezone
from hashlib import sha256
import jwt
import json
from flask import jsonify, request
import sys
sys.path.insert(0, 'utils/')
from utils.logger import setup_logger

logger = setup_logger("Main App:Auth")

# Load configuration from app_config.json
with open('app_config.json', 'r') as config_file:
    config = json.load(config_file)

PASSWORD = sha256(b'sudip').hexdigest()
JWT_SECRET = 'secret'

def portal_verify_token(token):   
    try:
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": True})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def check_user_login():
    token = request.headers.get('Authorization')
    if not portal_verify_token(token):
        logger.debug("Login Failure",request.json['data'])
        return jsonify({"success":False,"message": "Invalid token"}), 401
    logger.debug("Login Success",request.json['data'])
    return jsonify({"success":True,"message": "Data written successfully"}), 200

def portal_login():
    password = request.json['password']
    token = jwt.encode(
        {'password': password, 
         'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)}, 
         JWT_SECRET, 
         algorithm='HS256')
    if password == PASSWORD:
        return jsonify({"success": True, 'token': token})
    else:
        return jsonify({"success": False})
