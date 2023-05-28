
from flask import Flask, request
from flask_cors import CORS

from src.user.user_controller import user_app
from src.todo.todo_controller import todo_app
from src.import_data.import_data_controller import import_app
from src.collection.collection_controller import collection_app


app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(user_app)
app.register_blueprint(todo_app)
app.register_blueprint(import_app)
app.register_blueprint(collection_app)


if __name__ == '__main__':
    app.run()