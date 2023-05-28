import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime

import config

HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']

client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="test", user_agent_overwrite=True)
db = client.get_database_client(DATABASE_ID)
items_container = db.get_container_client(CONTAINER_ID)


def check_user_exists(uname):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.uname = @uname AND users.partitionKey=@partitionKey",
            parameters=[
                {"name":"@uname", "value": uname},
                {"name":"@partition", "value": "users"}],
            enable_cross_partition_query=True))
    except e:
        return False

    if len(response) == 0:
        return False
    return True

def check_mail_exists(mail):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.mail = @mail AND users.partitionKey=@partitionKey",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True))
    except e:
        return False
    
    if len(response) == 0:
        return False
    return True

def check_password(mail, passhash):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.mail = @mail AND users.partitionKey=@partitionKey",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True))
    except e:
        return False

    if response.pop().get('passhash') == passhash:
        return True
    return False

def read_items(ownerId):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.ownerId=@ownerId AND i.partitionKey=@partitionKey",
            parameters=[
                {"name":"@ownerId", "value": ownerId},
                {"name":"@partition", "value": "todo"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    except IndexError:
        response = "NotFound"
    finally:
        return response

def read_item(id, ownerId):
    try:
        item = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.id=@id AND i.ownerId=@ownerId AND i.partitionKey=@partitionKey",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@ownerId", "value": ownerId},
                {"name":"@partition", "value": "todo"}],
            enable_cross_partition_query=True)).pop(0)
    except exceptions.CosmosHttpResponseError:
        item = "ServerError"
    except IndexError:
        item = "NotFound"
    finally:
        return item


def get_user_by_id(id):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM users WHERE users.id=@id AND users.partitionKey=@partitionKey",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True)).pop();
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    except IndexError:
        response = "NotFound"
    finally:
        return response


def get_user_by_email(mail):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM users WHERE users.mail=@mail AND users.partitionKey=@partitionKey",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True)).pop();
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    except IndexError:
        response = "NotFound"
    finally:
        return response


def create_item(item):
    try:
        response = items_container.create_item(body=item)
    except exceptions.CosmosHttpResponseError as e:
        response = "Conflict"
    finally:
        return response


def update_user(id, new_user):
    user = get_user_by_id(id)
    if user == "ServerError" or user == "NotFound":
        return user
    user['uname'] = new_user['uname']
    user['mail'] = new_user['mail']
    user['passhash'] = new_user['passhash']
    user['msdata'] = new_user['msdata']
    try:
        response = items_container.replace_item(item=user, body=user)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response


def update_item(id, ownerId, update_item):
    item = read_item(id, ownerId)
    if item == "ServerError" or item == "NotFound":
        return item
    item['title'] = update_item['title']
    item['body'] = update_item['body']
    item['attachments'] = update_item['attachments']
    item['due_date'] = update_item['due_date']
    item['completed'] = update_item['completed']
    try:
        response = items_container.replace_item(item=item, body=item)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response


def delete_item(id):
    try:
        response = items_container.delete_item(item=str(id), partition_key='todo')
    except exceptions.CosmosHttpResponseError as e:
        response = 'NotFound'
    finally:
        return response