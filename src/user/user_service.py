import azure.cosmos.exceptions as exceptions

from db_ops import items_container


def create_user(user):
    try:
        response = items_container.create_item(user)
    except exceptions.CosmosHttpResponseError as e:
        response = "Conflict"
    finally:
        return response
    

def get_user_by_id(id):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM users WHERE users.id=@id AND users.partitionKey.partition=@partition",
            parameters=[
                {"name":"@id", "value": id},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True)).pop();
        return response
    except exceptions.CosmosHttpResponseError:
        return "ServerError"
    except IndexError:
        return "NotFound"


def get_user_data_by_email(mail):
    try:
        response = list(items_container.query_items(
            query="SELECT * FROM users WHERE users.data.email=@mail AND users.partitionKey.partition=@partition",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True)).pop();
        
        data = response['data']
        user = {
            "id": response["id"],
            "uname": data["uname"],
            "email": data["email"],
            "passhash": data["passhash"]
        }
        return user
    except exceptions.CosmosHttpResponseError:
        return "ServerError"
    except IndexError:
        return "NotFound"


def update_user(id, new_user):
    user = get_user_by_id(id)
    if user == "ServerError" or user == "NotFound":
        return user

    if "msdata" in new_user:
        msdata = new_user["msdata"]
    else:
        msdata = user.get('msdata')

    data = user['data']
    data = {
        "uname": new_user["uname"],
        "email": new_user["mail"],
        "passhash": new_user["passhash"],
        "msdata": msdata
    }
    user['data'] = data

    try:
        response = items_container.replace_item(item=user, body=user)
    except exceptions.CosmosHttpResponseError:
        response = "ServerError"
    finally:
        return response


def check_user_exists(uname):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.data.uname = @uname AND users.partitionKey.partition=@partition",
            parameters=[
                {"name":"@uname", "value": uname},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError as e:
        return False

    if len(response) == 0:
        return False
    return True


def check_mail_exists(mail):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.data.email = @mail AND users.partitionKey.partition=@partition",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError as e:
        return False
    
    if len(response) == 0:
        return False
    return True


def check_password(mail, passhash):
    try:
        response = list(items_container.query_items(
            query = "SELECT * FROM users WHERE users.data.email = @mail AND users.partitionKey.partition=@partition",
            parameters=[
                {"name":"@mail", "value": mail},
                {"name":"@partition", "value": "user"}],
            enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError as e:
        return False

    data = response.pop().get('data')

    if data['passhash'] == passhash:
        return True
    return False