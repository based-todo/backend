from flask import Blueprint, request, make_response
from azure.communication.email import EmailClient
import json
import jwt
import uuid
import datetime
import requests

from ..todo import todo_service
from ..user import user_service
import config

import_app = Blueprint('import_app', __name__)

@import_app.route('/api/v1/import/outlook', methods=['GET'])
def import_outlook():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    

    user = user_service.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = import_app.response_class(
            response=json.dumps({}),
            status=404,
            mimetype='application/json'
        )
    else:
        msdata = user.get('msdata')
        if msdata == None:
            response = make_response({}, 404)
        else:
            rsp = requests.get(f'https://graph.microsoft.com/v1.0/me/messages?$search="[TODO]"',
                headers={'Authorization': f'Bearer {msdata["msauth"]}'})
            if rsp.status_code != 200:
                return make_response({}, 500)
            data = rsp.json().get('value');
            if data == None:
                return make_response({}, 500)
            
            list_to_import = []
            for item in data:
                subj = item.get('subject')
                if(subj.startswith('[TODO]')):
                    subj = subj[7:]
                list_to_import.append(subj)
            
            for todo in list_to_import:
                item = {
                    'id': str(uuid.uuid4()),
                    'partition': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = todo_service.create_item(item)
                
            response =  make_response({}, 200)
    return response

@import_app.route('/api/v1/import/mstodo', methods=['GET'])
def import_mstodo():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    user = user_service.get_user_by_id(payload['id'])
    if user == "NotFound":
        response = make_response({}, 404)
    else:
        msdata = user.get('msdata')
        if msdata == None:
            response = make_response({}, 404) 
        else:
            rsp = requests.get(f'https://graph.microsoft.com/v1.0/me/todo/lists',
                headers={'Authorization': f'Bearer {msdata["msauth"]}'})
            
            if rsp.status_code != 200:
                return make_response({}, 500) 
            
            data = rsp.json().get('value');
            if data == None:
                return make_response({}, 200) 
            
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
                    'partition': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = todo_service.create_item(item)
            
            list_to_import = []
            
            for todo in list_to_import:
                item = {
                    'id': str(uuid.uuid4()),
                    'partition': 'todo',
                    'title': '',
                    'body': todo,
                    'attachments': [],
                    'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'due_date': datetime.now().isoformat(),
                    'completed': False,
                    'ownerId': payload['id']
                }

                db_response = todo_service.create_item(item)
                
            response = make_response({}, 200) 
    return response
