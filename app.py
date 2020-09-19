from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from pymongo import MongoClient

# to handle CORS error
from flask_cors import CORS

# handle .env
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
api = Api(app)

client = MongoClient("mongodb://localhost:27017")
db = client["todo"]
document = db["notes"]





if __name__ == "__main__":
    app.run(port = 5000)