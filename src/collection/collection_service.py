import azure.cosmos.exceptions as exceptions

from db_ops import items_container

def create_collection(collection):
    try:
        response = items_container.create_item(body=collection)
    except exceptions.CosmosHttpResponseError as e:
        response = "Conflict"
    finally:
        return response
    

def get_collection(id, ownerId):
    try:
        item = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.id=@id AND i.data.ownerId=@ownerId AND i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@ownerId", "value": ownerId},
                {"name":"@partition", "value": "collection"}],
            enable_cross_partition_query=True)).pop(0)
    except exceptions.CosmosHttpResponseError:
        item = "ServerError"
    except IndexError:
        item = "NotFound"
    finally:
        return item


def get_collection_unrestricted(id):
    try:
        item = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.id=@id AND i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@partition", "value": "collection"}],
            enable_cross_partition_query=True)).pop(0)
    except exceptions.CosmosHttpResponseError:
        item = "ServerError"
    except IndexError:
        item = "NotFound"
    finally:
        return item


def get_all_collections(ownerId):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.data.ownerId=@ownerId AND i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@ownerId", "value": ownerId},
                {"name":"@partition", "value": "collection"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    except IndexError:
        response = "NotFound"
    finally:
        return response


def get_all_collections_unrestricted():
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@partition", "value": "collection"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    except IndexError:
        response = "NotFound"
    finally:
        return response


def add_to_collection(collection, todo_id, ownerId):
    data = collection['data']
    items = data.get('items', [])
    items.append(todo_id)
    data['items'] = items
    collection['data'] = data

    try:
        response = items_container.replace_item(item=collection, body=collection)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response


def delete_from_collection(collection, todo_id, ownerId):
    data = collection['data']
    items = data.get('items', [])
    items.remove(todo_id)
    data['items'] = items
    collection['data'] = data

    try:
        response = items_container.replace_item(item=collection, body=collection)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response
    
def delete_collection(id):
    try:
        response = items_container.delete_item(item=str(id), partition_key='collection')
        return "Success"
    except exceptions.CosmosHttpResponseError as e:
        return 'NotFound'
    
def add_collection_access(collection, id):
    data = collection['data']
    if "viewers" in data.keys():
        viewers = data.get('viewers', [])
        if id not in viewers:
            viewers.add(id)
        else:
            return "Conflict"
    else:
        viewers = [id]
    data['viewers'] = viewers
    collection['data'] = data
    try:
        response = items_container.replace_item(item=collection, body=collection)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response
    

def remove_todo_access(collection, id):
    data = collection['data']
    if "viewers" in data.keys():
        viewers = data.get('viewers', [])
        if id in viewers:
            viewers.remove(id)
        else:
            return "NotFound"
    else:
        return "NotFound"
    data['viewers'] = viewers
    collection['data'] = data
    
    try:
        response = items_container.replace_item(item=collection, body=collection)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response
