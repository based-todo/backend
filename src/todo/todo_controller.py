from flask import Blueprint, request, make_response
from azure.communication.email import EmailClient
from azure.storage.blob import BlobServiceClient
import json
import jwt
import uuid
from datetime import datetime

import config
from . import todo_service

service = BlobServiceClient(account_url=f"https://{config.settings['blob_account_name']}.blob.core.windows.net",
                            credential=config.settings['blob_account_key'])


todo_app = Blueprint('todo_app', __name__)

@todo_app.route('/api/v1/todos', methods=['GET'])
def get_all():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    db_response = todo_service.read_items(payload['id'])
    if db_response == "ServerError":
         response = make_response({}, 500)
    elif db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response


@todo_app.route('/api/v1/todos/<id>')
def get_item(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    db_response = todo_service.read_item(id, payload['id'])
    if db_response == "ServerError":
         response = make_response({}, 500)
    elif db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response


@todo_app.route('/api/v1/todos', methods=['POST'])
def create_item():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    data = request.get_json();
    item = {
        'id': str(uuid.uuid4()),
        'partitionKey':{
            'partition': 'todo'
        },
        'data':{
            'title': data['title'],
            'body': data['body'],
            'attachments': data['attachments'],
            'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'due_date': data['due_date'],
            'completed': data['completed'],
            'ownerId': payload['id']
        }
    }

    db_response = todo_service.create_item(item)
    if db_response != "Conflict":
        response = make_response(db_response, 201)
    else:
        response = make_response({}, 409)
    return response


@todo_app.route('/api/v1/todos/<id>', methods=['PUT'])
def update_item(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    data = request.get_json()
    data = {
        'title': data['title'],
        'body': data['body'],
        'attachments': data['attachments'],
        'due_date': data['due_date'],
        'completed': data['completed']
    }

    db_response = todo_service.update_item(id, payload['id'], data)
    if db_response == "ServerError":
         response = make_response({}, 500)
    elif db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response


@todo_app.route('/api/v1/todos/<id>', methods=['DELETE'])
def delete_item(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    db_response = todo_service.delete_item(id)
    if db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response

@todo_app.route('/api/v1/blob', methods=['POST'])
def upload_blob():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    file = request.files.get('file')

    url = str(uuid.uuid4()) + file.filename
    blob = service.get_blob_client('images', url)
    
    raw = file.stream.read()
    data = blob.upload_blob(raw)

    return make_response({'url': f"https://{config.settings['blob_account_name']}.blob.core.windows.net/images/{url}"}, 201)


def create_response(load, status_code):
    response = make_response(json.dumps(load))
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json'

    return response