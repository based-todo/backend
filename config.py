import os

settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://treicrai-cosmosdb.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'I7rurdH2i73z39XH9vuJvVce61VIoa0cb3bsuFe5yiZ6yAdO8fCTYFB7aUWbfJEp8acLka1XnUDTACDbFRKlAA=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'ToDoList'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'Items'),
    'token_secret_key': os.environ.get('TOKEN_SECRET_KEY', 'alex'),
    'blob_account_name': os.environ.get('BLOB_ACCOUNT_NAME', 'treicrai2storage'),
    'blob_account_key': os.environ.get('BLOB_ACCOUNT_KEY', 'rSMFyTyiMkF/Ax4ZN0R7oU2AlUWKBUZ3jxMfrK/U3PZ6A7D+wtVQ3i7vm341VDw+zdPYjTTsWn2q+AStMXaGww=='),
    'email_connection_string': os.environ.get('EMAIL_CONNECTION_STRING', 'endpoint=https://treicrai-communication.communication.azure.com/;accesskey=yvG+ZPqXOwYPpBla/lk0YIUJmXgN0ljZL3bq5Op5HiYn54ysLfpxOIgY8fvZOqkykz9GxWrpp1c0eDQKEaRgDA==')
}