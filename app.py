from datetime import datetime
import uuid
from flask import Flask, request
import json
import jwt
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
import os
import requests
from azure.communication.email import EmailClient

import db_ops
import config

service = BlobServiceClient(account_url=f"https://{config.settings['blob_account_name']}.blob.core.windows.net",
                            credential=config.settings['blob_account_key'])

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
email_client = EmailClient.from_connection_string(config.settings['email_connection_string'])


@app.route('/api/v1/todos', methods=['GET'])
def get_all():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    db_response = db_ops.read_items(payload['id'])
    if db_response == "ServerError":
         response = app.response_class(
            response=json.dumps({}),
            status=500,
            mimetype='application/json'
        )
    elif db_response == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(db_response),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/api/v1/todos/<id>')
def get_item(id):
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    db_response = db_ops.read_item(id, payload['id'])
    if db_response == "ServerError":
         response = app.response_class(
            response=json.dumps({}),
            status=500,
            mimetype='application/json'
        )
    elif db_response == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(db_response),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/api/v1/todos', methods=['POST'])
def create_item():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )
    
    data = request.get_json();
    item = {
        'id': str(uuid.uuid4()),
        'partitionKey': 'todo',
        'title': data['title'],
        'body': data['body'],
        'attachments': data['attachments'],
        'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'due_date': data['due_date'],
        'completed': data['completed'],
        'ownerId': payload['id']
    }

    db_response = db_ops.create_item(item)
    if db_response != "Conflict":
        response = app.response_class(
            response=json.dumps(db_response),
            status=201,
            mimetype='application/json')
    else:
        response = app.response_class(
            response=json.dumps({}),
            status=409,
            mimetype='application/json')
    return response


@app.route('/api/v1/todos/<id>', methods=['PUT'])
def update_item(id):
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    data = request.get_json()
    item = {
        'title': data['title'],
        'body': data['body'],
        'attachments': data['attachments'],
        'due_date': data['due_date'],
        'completed': data['completed']
    }

    db_response = db_ops.update_item(id, payload['id'], item)
    if db_response == "ServerError":
         response = app.response_class(
            response=json.dumps({}),
            status=500,
            mimetype='application/json'
        )
    elif db_response == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(db_response),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/api/v1/todos/<id>', methods=['DELETE'])
def delete_item(id):
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )
    
    db_response = db_ops.delete_item(id)
    if db_response == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(db_response),
            status=200,
            mimetype='application/json'
        )
    return response

@app.route('/api/v1/blob', methods=['POST'])
def upload_blob():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    file = request.files.get('file')

    url = str(uuid.uuid4()) + file.filename
    blob = service.get_blob_client('images', url)
    
    raw = file.stream.read()
    data = blob.upload_blob(raw)

    return app.response_class(
        response=json.dumps({'url': f"https://{config.settings['blob_account_name']}.blob.core.windows.net/images/{url}"}),
        status=201,
        mimetype='application/json'
    )

def create_user(data):
    user = {
        'id': str(uuid.uuid4()),
        'partitionKey': 'user',
        'uname': data['uname'],
        'passhash': data['passhash'],
        'mail': data['mail']
    }

    db_response = db_ops.create_item(user)
    if db_response != "Conflict":
        response = app.response_class(
            response=json.dumps(db_response),
            status=201,
            mimetype='application/json')
    else:
        response = app.response_class(
            response=json.dumps({}),
            status=409,
            mimetype='application/json')
    return response

@app.route('/api/v1/register', methods=['POST'])
def register():
    user = request.json

    uname = user.get('uname')
    mail = user.get('mail')

    username_exists = db_ops.check_user_exists(uname)
    email_exists = db_ops.check_mail_exists(mail)

    if username_exists or email_exists:
        conflict_type = ""
        if username_exists:
            conflict_type = "username"
        else:
            conflict_type = "email"

        response = {
            "conflictType": conflict_type
        }
        return app.response_class(json.dumps(response), status=409, mimetype='application/json')

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
    email_client.begin_send(message)
    return create_user(user)


@app.route('/api/v1/login', methods=['POST'])
def login():
    email = request.json.get('mail')
    passhash = request.json.get('passhash')
    
    if not db_ops.check_mail_exists(email):
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
        )

    if not db_ops.check_password(email, passhash):
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
        )
    user = db_ops.get_user_by_email(email)

    payload = {'id': user.get('id')}
    token = jwt.encode(payload, config.settings['token_secret_key'], algorithm='HS256')
    return app.response_class(
        response=json.dumps({'token': token.decode('utf-8')}),
        status=200,
        mimetype='application/json'
    )


@app.route('/api/v1/user', methods=['GET'])
def get_user():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    user = db_ops.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(user),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/api/v1/msdata', methods=['POST'])
def add_ms_data():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    user = db_ops.get_user_by_id(payload['id'])
    user['msdata'] = request.json
    db_response = db_ops.update_user(payload['id'], user)
    if db_response == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps(db_response),
            status=200,
            mimetype='application/json'
        )
    return response


@app.route('/api/v1/import/outlook', methods=['GET'])
def import_outlook():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    user = db_ops.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        msdata = user.get('msdata')
        if msdata == None:
            response = app.response_class(
                response=json.dumps({}),
                status=404,
                mimetype='application/json'
            )
        else:
            rsp = requests.get(f'https://graph.microsoft.com/v1.0/me/messages?$search="[TODO]"',
                headers={'Authorization': f'Bearer {msdata["msauth"]}'})
            if rsp.status_code != 200:
                return app.response_class(
                    response=json.dumps({}),
                    status=500,
                    mimetype='application/json'
                )
            data = rsp.json().get('value');
            if data == None:
                return app.response_class(
                    response=json.dumps({}),
                    status=500,
                    mimetype='application/json'
                )
            
            list_to_import = []
            for item in data:
                subj = item.get('subject')
                if(subj.startswith('[TODO]')):
                    subj = subj[7:]
                list_to_import.append(subj)
            
            for todo in list_to_import:
                item = {
                    'id': str(uuid.uuid4()),
                    'partitionKey': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = db_ops.create_item(item)
                
            response = app.response_class(
                response=json.dumps({}),
                status=200,
                mimetype='application/json'
            )
    return response



@app.route('/api/v1/import/mstodo', methods=['GET'])
def import_mstodo():
    token = request.headers.get('Authorization')
    if not token:
        return app.response_class(
            response=json.dumps({}),
            status=401,
            mimetype='application/json'
    )
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return app.response_class(
            response=json.dumps({}),
            status=403,
            mimetype='application/json'
    )

    user = db_ops.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        msdata = user.get('msdata')
        if msdata == None:
            response = app.response_class(
                response=json.dumps({}),
                status=404,
                mimetype='application/json'
            )
        else:
            rsp = requests.get(f'https://graph.microsoft.com/v1.0/me/todo/lists',
                headers={'Authorization': f'Bearer {msdata["msauth"]}'})
            
            if rsp.status_code != 200:
                return app.response_class(
                    response=json.dumps({}),
                    status=500,
                    mimetype='application/json'
                )
            
            data = rsp.json().get('value');
            if data == None:
                return app.response_class(
                    response=json.dumps({}),
                    status=200,
                    mimetype='application/json'
                )
            
            lists_ids = []
            for item in data:
                lists_ids.append(item.get('id'))

            list_to_import = []
            for list_id in lists_ids:
                rsp = requests.get(f'https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks',
                    headers={'Authorization': f'Bearer {msdata["msauth"]}'})
                if rsp.status_code != 200:
                    continue
                data = rsp.json().get('value');
                if data == None:
                    continue
            
                for item in data:
                    list_to_import.append(item.get('title'))
            
            for todo in list_to_import:
                item = {
                    'id': str(uuid.uuid4()),
                    'partitionKey': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = db_ops.create_item(item)
            
            list_to_import = []
            
            for todo in list_to_import:
                item = {
                    'id': str(uuid.uuid4()),
                    'partitionKey': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = db_ops.create_item(item)
                
            response = app.response_class(
                response=json.dumps({}),
                status=200,
                mimetype='application/json'
            )
    return response

if __name__ == '__main__':
    app.run()