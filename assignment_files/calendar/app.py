from flask import Flask, request
from flask_restful import Resource, Api
import psycopg2
import json

app = Flask(__name__)
api = Api(app)

# Database configuration
DB_HOST = 'calendar_persistence'
DB_PORT = '5432'
DB_NAME = 'calendar_database'
DB_USER = 'admin'
DB_PASSWORD = 'docker'

# Connect to the database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    host=DB_HOST,
    password=DB_PASSWORD,
    port=DB_PORT
)
cursor = conn.cursor()

class Calendar(Resource):
    def get(self, owner):
        try:
            # Retrieve the event ID list for the specified owner
            cursor.execute("SELECT event_id_list FROM calendar WHERE owner = %s", (owner,))
            result = cursor.fetchone()
            if result:
                event_id_list = result[0]
                return {'owner': owner, 'event_id_list': event_id_list}, 200
            else:
                return {'error': 'Owner not found'}, 404
        except psycopg2.Error as e:
            return {'error': str(e)}, 500

class ShareCalendar(Resource):
    def post(self, owner):
        try:
            # Get the username to share the calendar with from the request
            data = request.get_json()
            shared_username = data.get('username')

            # Check if the owner exists in the database
            cursor.execute("SELECT * FROM calendar WHERE owner = %s", (owner,))
            owner_exists = cursor.fetchone()
            if not owner_exists:
                return {'error': 'Owner not found'}, 404

            # Check if the username to share with exists in the database
            cursor.execute("SELECT * FROM calendar WHERE owner = %s", (shared_username,))
            shared_user_exists = cursor.fetchone()
            if not shared_user_exists:
                return {'error': 'Shared user not found'}, 404

            # Add the shared username to the calendar_share_list of the owner
            cursor.execute("UPDATE calendar SET calendar_share_list = array_append(calendar_share_list, %s) WHERE owner = %s", (shared_username, owner))
            conn.commit()

            return {'message': 'Calendar shared successfully'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500
class CreateCalendar(Resource):
    def post(self):
        try:
            data = request.get_json()
            owner = data.get('owner')
            event_id_list = data.get('event_id_list', [])
            calendar_share_list = data.get('calendar_share_list', [])

            cursor.execute("INSERT INTO calendar (owner, event_id_list, calendar_share_list) VALUES (%s, %s, %s)",
                           (owner, event_id_list, calendar_share_list))
            conn.commit()

            return {'message': 'Calendar created successfully'}, 201
        except Exception as e:
            return {'error': str(e)}, 500

class AddToCalendar(Resource):
    def post(self, owner):
        try:
            # Get the event ID from the request data
            data = request.get_json()
            event_id = data.get('event_id')

            # Update the event ID list of the owner with the new event ID
            cursor.execute("UPDATE calendar SET event_id_list = array_append(event_id_list, %s) WHERE owner = %s", (event_id, owner))
            conn.commit()

            return {'message': 'Event added to calendar successfully'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500

class getAllowedUsers(Resource):
    def get(self,owner):
        cursor.execute("SELECT calendar_share_list FROM calendar WHERE owner = %s", (owner,))
        found_list = cursor.fetchone()[0]
        return {'calendar_share_list': found_list}, 200


        
        

api.add_resource(CreateCalendar, '/calendar')
api.add_resource(ShareCalendar, '/calendar/<string:owner>/share')
api.add_resource(Calendar, '/calendar/<string:owner>')
api.add_resource(AddToCalendar, '/calendar/<string:owner>/add')
api.add_resource(getAllowedUsers,'/calendar/shared/<string:owner>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')