from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2

app = Flask(__name__)
api = Api(app)

# Database configuration
DB_HOST = 'db'
DB_PORT = '5432'
DB_NAME = 'authentication_db'
DB_USER = 'admin'
DB_PASSWORD = 'docker'

conn = psycopg2.connect(
    dbname=DB_NAME, 
    user=DB_USER, 
    host=DB_HOST, 
    password=DB_PASSWORD, 
    port=DB_PORT
)
cursor = conn.cursor()

# Endpoint for user registration
class Register(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required',location ='form')
        parser.add_argument('password', type=str, required=True, help='Password is required',location ='form')
        args = parser.parse_args()
        
        username = args['username']
        password = args['password']
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            return {'error': 'Username already exists'}, 400
        
        # Insert new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        
        return {'message': 'User registration successful'}, 201

# Endpoint for user login
class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required',location ='form')
        parser.add_argument('password', type=str, required=True, help='Password is required',location ='form')
        args = parser.parse_args()
        
        username = args['username']
        password = args['password']
        
        # Retrieve user from the database
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        if user:
            return {'message': 'Login successful'}, 200
        else:
            return {'error': 'Invalid username or password'}, 401

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
