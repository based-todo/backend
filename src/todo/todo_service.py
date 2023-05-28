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