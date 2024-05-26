from flask import Flask, request
from flask_restful import Resource, Api
import psycopg2
import json

app = Flask(__name__)
api = Api(app)

# Database configuration
DB_HOST = 'event_persistence'
DB_PORT = '5432'
DB_NAME = 'event_database'
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

# Endpoint for retrieving all public events
class PublicEvents(Resource):
    def get(self):
        try:
            # Query public events from the database
            cursor.execute("SELECT id, title, event_date, owner FROM events WHERE event_type = 'public'")
            public_events = cursor.fetchall()

            # Format the results as (id, title, date, organizer) tuples
            events_list = [(event[1], str(event[2]), event[3],event[0]) for event in public_events]

            return {'public_events': events_list}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class CreateEvent(Resource):
    def post(self):
        try:
            # Get event details from request
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')
            date = data.get('date')
            event_type = data.get('event_type')
            owner = data.get('owner')

            cursor.execute(
                "INSERT INTO events (owner, title, description, event_date, event_type) VALUES (%s, %s, %s, %s, %s) RETURNING id::text",
                (owner, title, description, date, event_type)
            )
            event_id = cursor.fetchone()[0]  # Get the id of the inserted row
            conn.commit()

            return {'message': 'Event created successfully', 'id': event_id}, 201

        except Exception as e:
            return {'error': str(e)}, 500

class EventDetail(Resource):
    def get(self, event_id):
        try:
            # Query the event details from the events table
            cursor.execute("SELECT title, event_date, owner, event_type FROM events WHERE id = %s", (event_id,))
            event = cursor.fetchone()

            if not event:
                return {'error': 'Event not found'}, 404

            title, event_date, owner, event_type = event
            event_date = str(event_date)

            # Format the as it is described in the gui
            event_detail = [title, event_date, owner, event_type.capitalize()]

            return {'event': event_detail}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class MultipleEventDetail(Resource):
    def post(self):
        try:
            # Get the list of event IDs from the query parameters
            event_ids = request.json.get('event_ids', [])

            # Initialize a list to store event details
            event_details = []

            for event_id in event_ids:
                # Query the event details from the events table
                cursor.execute("SELECT id, title, event_date, owner, event_type FROM events WHERE id = %s", (event_id,))
                event = cursor.fetchone()

                if event:
                    # Format the event details
                    event_id, title, event_date, owner, event_type = event
                    event_date = str(event_date)
                    event_detail = {'id': event_id, 'title': title, 'event_date': event_date, 'owner': owner, 'event_type': event_type.capitalize()}
                    event_details.append(event_detail)

            return {'events': event_details}, 200
        except Exception as e:
            return {'error': str(e)}, 500


# Add resources to API
api.add_resource(CreateEvent, '/create-event')
api.add_resource(PublicEvents, '/public-events')
api.add_resource(EventDetail, '/event/<int:event_id>')
api.add_resource(MultipleEventDetail, '/events')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
