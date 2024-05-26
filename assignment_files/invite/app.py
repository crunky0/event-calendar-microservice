from flask import Flask, request
from flask_restful import Resource, Api
import psycopg2

app = Flask(__name__)
api = Api(app)

# Database configuration
DB_HOST = 'invite_persistence'
DB_PORT = '5432'
DB_NAME = 'invite_database'
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


class CreateInvite(Resource):
    def post(self):
        try:
            data = request.get_json()
            event_id = data.get('event_id')
            users = data.get('users')
            owner = data.get('owner')

            # Add invites to the database for each user
            for user in users:
                cursor.execute("INSERT INTO invites (event_id, username, invitation_status) VALUES (%s, %s, %s)", (event_id, user, 'Pending'))

            # Add the owner to the invites with the status 'Participating'
            cursor.execute("INSERT INTO invites (event_id, username, invitation_status) VALUES (%s, %s, %s)", (event_id, owner, 'Participating'))

            conn.commit()
            return {'message': 'Invites created successfully'}, 201
        except psycopg2.Error as e:
            return {'error': str(e)}, 500



class ChangeStatus(Resource):
    def post(self):
        try:
            data = request.get_json()
            event_id = data.get('event_id')
            user = data.get('user')
            answer = data.get('answer')

            # Update invitation status
            cursor.execute("UPDATE invites SET invitation_status = %s WHERE event_id = %s AND username = %s",
                           (answer, event_id, user))
            conn.commit()
            return {'message': 'Invitation status updated successfully'}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500

class ShowPending(Resource):
    def get(self, username):
        try:

            cursor.execute("SELECT event_id FROM invites WHERE username = %s AND invitation_status = 'Pending'", (username,))
            event_ids = [row[0] for row in cursor.fetchall()]
            return {'pending_event_ids': event_ids}, 200
        
        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")  # Log the error
            return {'error': str(e)}, 500

class GetInvitationStatus(Resource):
    def get(self, event_id):
        try:
            cursor.execute("SELECT username, invitation_status FROM invites WHERE event_id = %s AND (invitation_status = 'Participating' OR invitation_status = 'Maybe Participating')", (event_id,))
            result = cursor.fetchall()
            user_statuses = [[row[0], row[1]] for row in result]
            return {'user_statuses': user_statuses}, 200
        except psycopg2.Error as e:
            return {'error': str(e)}, 500

class SingleInviteStatus(Resource):
    def get(self):
        try:
            # Extract event ID and username from the request query parameters
            event_id = request.args.get('event_id')
            username = request.args.get('username')

            # Query the invite status from the database
            cursor.execute("SELECT invitation_status FROM invites WHERE event_id = %s AND username = %s", (event_id, username))
            invite_status = cursor.fetchone()

            if invite_status:
                # Return the invite status if found
                return {'invitation_status': invite_status[0]}, 200
            else:
                # Return an error if invite status is not found
                return {'error': 'Invite status not found'}, 404
        except psycopg2.Error as e:
            # Handle database errors
            return {'error': str(e)}, 500


api.add_resource(SingleInviteStatus, '/invites/status')
api.add_resource(GetInvitationStatus, '/get-invitation-status/<string:event_id>')
api.add_resource(CreateInvite, '/create-invite')
api.add_resource(ChangeStatus, '/change-status')
api.add_resource(ShowPending, '/show-pending/<string:username>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
