import azure.cosmos.exceptions as exceptions

from db_ops import items_container


def read_items(ownerId):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.data.ownerId=@ownerId AND i.partitionKey.partition=@partition",
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


def read_items_unrestricted():
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.partitionKey.partition=@partition",
            parameters=[
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
            query="SELECT * FROM i WHERE i.id=@id AND i.data.ownerId=@ownerId AND i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@ownerId", "value": ownerId},
                {"name":"@partition", "value": "todo"}],
            enable_cross_partition_query=True)).pop(0)
        return item
    except exceptions.CosmosHttpResponseError:
        return "ServerError"
    except IndexError:
        return "NotFound"
        

def read_item_unrestricted(id):
    try:
        item = list(items_container.query_items(
            query="SELECT * FROM i WHERE i.id=@id AND i.partitionKey.partition=@partition",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@partition", "value": "todo"}],
            enable_cross_partition_query=True)).pop(0)
        return item
    except exceptions.CosmosHttpResponseError:
        return "ServerError"
    except IndexError:
        return "NotFound"


def create_item(item):
    try:
        response = items_container.create_item(body=item)
    except exceptions.CosmosHttpResponseError as e:
        response = "Conflict"
    finally:
        return response


def update_item(id, ownerId, data):
    item = read_item(id, ownerId)
    if item == "ServerError" or item == "NotFound":
        return item
    
    item['data'] = data
    try:
        response = items_container.replace_item(item=item, body=item)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response


def delete_item(id):
    try:
        response = items_container.delete_item(item=str(id), partition_key='todo')
        return "Success"
    except exceptions.CosmosHttpResponseError as e:
        return 'NotFound'
    

def add_todo_access(todo, id):
    data = todo['data']
    if "viewers" in data.keys():
        viewers = data.get('viewers', [])
        if id not in viewers:
            viewers.append(id)
        else:
            return "Conflict"
    else:
        viewers = [id]
    data['viewers'] = viewers
    todo['data'] = data
    
    try:
        response = items_container.replace_item(item=todo, body=todo)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response
    
def remove_todo_access(todo, id):
    data = todo['data']
    if "viewers" in data.keys():
        viewers = data.get('viewers', [])
        if id in viewers:
            viewers.remove(id)
        else:
            return "NotFound"
    else:
        return "NotFound"
    data['viewers'] = viewers
    todo['data'] = data
    
    try:
        response = items_container.replace_item(item=todo, body=todo)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response