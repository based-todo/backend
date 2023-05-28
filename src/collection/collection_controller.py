from flask import Blueprint, request, make_response
from datetime import datetime
import jwt
import json
import uuid

import config
from . import collection_service
from ..todo import todo_service

collection_app = Blueprint('collection_app', __name__)


@collection_app.route('/api/v1/collections/<id>', methods=['GET'])
def get_collection(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    collection = collection_service.get_collection(id, payload['id'])
    if collection == "ServerError":
        return make_response({}, 500)
    elif collection == "NotFound":
        collection = collection_service.get_collection_unrestricted(id)
        data = collection['data']
        if data.get('viewers') != None and payload['id'] in data['viewers']:
            return make_response(collection, 200)
        return make_response({'message': "Collection Not Found"}, 404)
    else:
        return make_response(collection, 200)


@collection_app.route('/api/v1/collections', methods=['GET'])
def get_all_collections():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    db_response = collection_service.get_all_collections(payload['id'])
    if db_response == "ServerError":
        return make_response({}, 500)
    
    my_collections = db_response
    collections = collection_service.get_all_collections_unrestricted()
    for collection in collections:
        print(collection)
        data = collection['data']
        print(data)
        if data.get('viewers') != None and payload['id'] in data['viewers']:
            my_collections.append(collection)
    return make_response(my_collections, 201)
    

@collection_app.route('/api/v1/collections/todos/<id>', methods=['GET'])
def get_todos_of_collection(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    collection = collection_service.get_collection(id, payload['id'])
    if collection == "ServerError":
        return make_response({}, 500)
    elif collection == "NotFound":
        collection = collection_service.get_collection_unrestricted(id)
        data = collection['data']
        if data.get('viewers') != None and payload['id'] in data['viewers']:
            return make_response(collection, 200)
        return make_response({'message': "Collection Not Found"}, 404)
    
    data = collection['data']
    items = data.get('items', [])

    todos = []
    for item in items:
        todo = todo_service.read_item(item, payload['id'])
        if todo == "ServerError":
            return make_response({}, 500)
        todos.append(todo)
    return make_response(todos, 200)
   


@collection_app.route('/api/v1/collections', methods=['POST'])
def create_collection():
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    data = request.get_json()
    collection = {
        'id': str(uuid.uuid4()),
        'partitionKey':{
            'partition': 'collection',
        },
        'data':{
            'name': data['name'],
            'description': data['description'],
            'created_on': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'ownerId': payload['id'],
            'items': []
        }
    }

    db_response = collection_service.create_collection(collection)
    if db_response != "Conflict":
        response = make_response(db_response, 201)
    else:
        response = make_response({}, 409)
    return response


@collection_app.route('/api/v1/collections/todos/<id>', methods=['POST'])
def add_to_collection(id):
    token = request.headers.get("Authorization")
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    collection = collection_service.get_collection(id, payload['id'])
    if collection == "ServerError":
        return make_response({}, 500)
    elif collection == "NotFound":
        return make_response({'message': "Collection Not Found"}, 404)

    todo_id = request.get_json()['todo_id']
    db_response = todo_service.read_item(todo_id, payload['id'])
    if db_response == "ServerError":
        return make_response({}, 500)
    elif db_response == "NotFound":
        return make_response({'message': "Todo Not Found"}, 404)

    db_response = collection_service.add_to_collection(collection, todo_id, payload['id'])
    if db_response == "ServerError":
        return make_response({}, 500)
    else:
        return make_response(db_response, 201)


@collection_app.route('/api/v1/collections/todos/<id>', methods=['DELETE'])
def remove_from_collection(id):
    token = request.headers.get("Authorization")
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    collection = collection_service.get_collection(id, payload['id'])
    if collection == "ServerError":
        return make_response({}, 500)
    elif collection == "NotFound":
        return make_response({'message': "Collection Not Found"}, 404)

    todo_id = request.get_json()['todo_id']
    db_response = todo_service.read_item(todo_id, payload['id'])
    if db_response == "ServerError":
        return make_response({}, 500)
    elif db_response == "NotFound":
        return make_response({'message': "Todo Not Found"}, 404)
    
    data = collection['data']
    items = data.get('items', [])
    if todo_id not in items:
        return make_response({}, 404)
    
    db_response = collection_service.delete_from_collection(collection, todo_id, payload['id'])
    if db_response == "ServerError":
        return make_response({}, 500)
    else:
        return make_response(db_response, 200)


@collection_app.route('/api/v1/collections/<id>', methods=['DELETE'])
def remove_collection(id):
    token = request.headers.get("Authorization")
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 
    
    db_response = collection_service.delete_collection(id)
    if db_response == 'NotFound':
        return make_response({}, 404)
    else:
        return make_response({}, 200)
    

@collection_app.route('/api/v1/collections/access/<id>', methods=['POST'])
def add_collection_access(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403) 

    collection = collection_service.get_collection_unrestricted(id)
    if collection == "ServerError":
         response = make_response({}, 500)
    elif collection == "NotFound":
        response = make_response({"message": "Collection not found"}, 404)
    
    db_response = collection_service.add_collection_access(collection, payload['id'])
    if db_response == "ServerError":
         response = make_response({}, 500)
    elif db_response == "Conflict":
        response = make_response({}, 409)
    else:
        response = make_response(db_response, 200)
    return response


@collection_app.route('/api/v1/collections/access/<id>', methods=['PUT'])
def remove_collection_access(id):
    token = request.headers.get('Authorization')
    
    if not token:
        return make_response({}, 401)
    try:
        payload = jwt.decode(token, config.settings['token_secret_key'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return make_response({}, 403)
    
    collection = collection_service.get_collection_unrestricted(id)
    if collection == "ServerError":
         response = make_response({}, 500)
    elif collection == "NotFound":
        response = make_response({"message": "Collection not found"}, 404)
    
    db_response = collection_service.remove_collection_access(collection, payload['id'])
    if db_response == "ServerError":
         response = make_response({}, 500)
    elif db_response == "NotFound":
        response = make_response({}, 404)
    else:
        response = make_response(db_response, 200)
    return response