
from flask import Blueprint, request, make_response
from azure.communication.email import EmailClient
import json
import jwt
import uuid

import config
from . import user_service

# email_client = EmailClient.from_connection_string(config.settings['email_connection_string'])

user_app = Blueprint('user_app', __name__)

@user_app.route('/api/v1/register', methods=['POST'])
def register():
    user = request.get_json()

    uname = user.get('uname')
    mail = user.get('mail')

    username_exists = user_service.check_user_exists(uname)
    email_exists = user_service.check_mail_exists(mail)

    if username_exists or email_exists:
        conflict_type = ""
        if username_exists:
            conflict_type = "username"
        else:
            conflict_type = "email"
 
        return create_response({"conflictType": conflict_type}, 409)
    
    message = {
        "content": {
            "subject": "Welcome to Todoer",
            "plainText": "Your registration was succesful",
            "html": f"<html><h1>You are the best, {uname}!</h1></html>"
        },
        "recipients": {
            "to": [
                {
                    "address": mail,
                    "displayName": uname
                }
            ]
        },
        "senderAddress": "DoNotReply@2f12238d-e6dc-4597-a8bb-adc4e9c05f61.azurecomm.net"
    }
    # email_client.begin_send(message)
    return create_user(user)

@user_app.route('/api/v1/login', methods=['POST'])
def login():
    user_login = request.get_json()

    email = user_login.get('mail')
    passhash = user_login.get('passhash')
    
    if not user_service.check_mail_exists(email):
        return make_response({}, 404) 

    if not user_service.check_password(email, passhash):
        return make_response({}, 401)
    
    user = user_service.get_user_data_by_email(email)
    if user in ["NotFound", "ServerError"]:
        return make_response({}, 404)

    payload = {'id': user.get('id')}
    token = jwt.encode(payload, config.settings['token_secret_key'], algorithm='HS256')
    return make_response({'token': token.decode('utf-8')}, 200) 


@user_app.route('/api/v1/user', methods=['PUT'])
def update_user():
    token = request.headers.get('Authorization')
    if not token:
        return make_response({}, 401)
  
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return  make_response({}, 403)
    
    user = user_service.get_user_by_id(payload['id'])
    if user == "NotFound":
        return make_response({}, 404)
    
    new_user = request.get_json()
    db_response = user_service.update_user(payload['id'], new_user)
    if db_response == "ServerError":
        return make_response({}, 500)
    else:
        return make_response(db_response, 200)


@user_app.route('/api/v1/user', methods=['GET'])
def get_user():
    token = request.headers.get('Authorization')
    if not token:
        return make_response({}, 401)
  
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return  make_response({}, 403)

    user = user_service.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(user, 200)
    return response


@user_app.route('/api/v1/msdata', methods=['POST'])
def add_ms_data():
    token = request.headers.get('Authorization')
    if not token:
        return make_response({}, 401)
  
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return  make_response({}, 403)

    user = user_service.get_user_by_id(payload['id'])
    user['msdata'] = request.get_json()
    db_response = user_service.update_user(payload['id'], user)
    if db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response



def create_user(data):
    user = {
        'id': str(uuid.uuid4()), 
        "partitionKey": {
            "partition": "user"
        },
        "data": {
            "uname": data['uname'],
            "email": data['mail'],
            "passhash": data['passhash']
        }
    }

    db_response = user_service.create_user(user)
    if db_response != "Conflict":
        response = create_response(db_response, 201)
    else:
        response = create_response(db_response, 409)
    return response


def create_response(load, status_code):
    response = make_response(json.dumps(load))
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json'

    return response