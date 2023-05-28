import os

settings = {
    'host': os.environ.get('ACCOUNT_HOST', ''),
    'master_key': os.environ.get('ACCOUNT_KEY', ''),
    'database_id': os.environ.get('COSMOS_DATABASE', ''),
    'container_id': os.environ.get('COSMOS_CONTAINER', ''),
    'token_secret_key': os.environ.get('TOKEN_SECRET_KEY', ''),
    'blob_account_name': os.environ.get('BLOB_ACCOUNT_NAME', ''),
    'blob_account_key': os.environ.get('BLOB_ACCOUNT_KEY', ''),
    'email_connection_string': os.environ.get('EMAIL_CONNECTION_STRING', '')
}