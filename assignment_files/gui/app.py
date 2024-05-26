from flask import Flask, render_template, redirect, request, url_for
import requests

app = Flask(__name__)


# The Username & Password of the currently logged-in User, this is used as a pseudo-cookie, as such this is not session-specific.
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return session_data.pop(key) if key in session_data else None  # Pop to ensure that it is only used once


def succesful_request(r):
    return r.status_code == 200


EVENT_SERVICE_URL = 'http://event_service:5000'
CALENDAR_SERVICE_URL = "http://calendar_service:5000"
INVITE_SERVICE_URL = "http://invite_service:5000"

@app.route("/")
def home():
    global username

    # Check if the user is logged in
    if username is None:
        # If not logged in, show the login page
        return render_template('login.html', username=username, password=password)
    else:
        try:
            # Try to get the list of public events from the event service
            response = requests.get(f"{EVENT_SERVICE_URL}/public-events")
            if response.status_code == 200:
                public_events = response.json().get('public_events', [])
            else:
                # If the request fails, set public events to an empty list
                public_events = []
        except requests.RequestException as e:
            # Handle network errors by setting public events to an empty list
            public_events = []

        # Render the home page with the public events
        return render_template('home.html', username=username, password=password, events=public_events)


@app.route("/event", methods=['POST'])
def create_event():
    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    publicprivate = request.form['publicprivate']
    invites = request.form['invites']
    owner = username

    # Split the invites string into a list of usernames
    invites_list = [invite.strip() for invite in invites.split(';') if invite.strip()]

    try:
        # Send a request to create the event
        response = requests.post(f"{EVENT_SERVICE_URL}/create-event", json={
            'owner': owner,
            'title': title,
            'description': description,
            'date': date,
            'event_type': publicprivate,
        })

        if response.status_code == 201:
            event_id = response.json().get('id')
            if not event_id:
                print("Event ID not returned in response")
                return render_template('error.html', message='Failed to retrieve event ID')

            print(f"Event created successfully with ID: {event_id}")

            # Add the event to the user's calendar
            calendar_response = requests.post(f"{CALENDAR_SERVICE_URL}/calendar/{owner}/add", json={'event_id': event_id})
            if calendar_response.status_code == 201:
                # Send invites to the list of users
                invite_response = requests.post(f"{INVITE_SERVICE_URL}/create-invite", json={
                    'event_id': event_id,
                    'users': invites_list,
                    'owner': username
                })
                if invite_response.status_code == 201:
                    # If invites are sent successfully, redirect to home
                    return redirect('/')
                else:
                    print(f"Failed to send invites: {invite_response.text}")
                    return render_template('error.html', message='Failed to send invites')
            else:
                print(f"Failed to add event to calendar: {calendar_response.text}")
                return render_template('error.html', message='Failed to add event to calendar')
        else:
            print(f"Failed to create event: {response.text}")
            return render_template('error.html', message='Failed to create event')
    except requests.RequestException as e:
        print(f"Network error: {str(e)}")
        return render_template('error.html', message='Failed to communicate with the event service')


@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    # Determine which user's calendar to display
    calendar_user = request.form['calendar_user'] if 'calendar_user' in request.form else username
    event_list = []
    success = False

    if calendar_user == username:
        # Fetch the logged-in user's calendar
        response = requests.get(f"{CALENDAR_SERVICE_URL}/calendar/{username}")
        if response.ok:
            try:
                event_list = response.json().get('event_id_list', [])
                success = True
            except ValueError:
                print("Invalid JSON response")
    else:
        # Fetch shared calendar
        response_allow = requests.get(f"{CALENDAR_SERVICE_URL}/calendar/shared/{calendar_user}")
        if response_allow.ok:
            try:
                allowed_users = response_allow.json().get('calendar_share_list', [])
                if username in allowed_users:
                    response = requests.get(f"{CALENDAR_SERVICE_URL}/calendar/{calendar_user}")
                    if response.ok:
                        try:
                            event_list = response.json().get('event_id_list', [])
                            success = True
                        except ValueError:
                            print("Invalid JSON response")
            except ValueError:
                print("Invalid JSON response")

    events = []
    
    if success:
        # Get details of the events
        response = requests.post(f"{EVENT_SERVICE_URL}/events", json={'event_ids': event_list})
        if response.ok:
            try:
                details_raw = response.json().get('events', [])
                for event in details_raw:
                    # Fetch invite status for each event
                    curr_response = requests.get(f"{INVITE_SERVICE_URL}/invites/status?event_id={event['id']}&username={calendar_user}")
                    if curr_response.ok:
                        try:
                            status = curr_response.json().get('invitation_status', 'yokki')
                            if status == "Participating":
                                status = "Going"
                            elif status == "Maybe Participating":
                                status = "Maybe Going"
                            event['status'] = status
                        except ValueError:
                            event['status'] = 'Unknown'
                    else:
                        event['status'] = 'Unknown'
                events = details_raw
                calendar = [(event['id'], event['title'], event['event_date'], event['owner'], event['status'].capitalize(), event['event_type'].capitalize()) for event in events]
            except ValueError:
                calendar = None
        else:
            calendar = None
    else:
        calendar = None

    return render_template('calendar.html', username=username, password=password, calendar_user=calendar_user, calendar=calendar, success=success)


@app.route('/share', methods=['GET'])
def share_page():
    # Render the share page
    return render_template('share.html', username=username, password=password, success=None)

@app.route('/share', methods=['POST'])
def share():
    shared_username = request.form['username']

    try:
        owner = username  
        # Send a request to share the calendar
        response = requests.post(f"{CALENDAR_SERVICE_URL}/calendar/{owner}/share", json={'username': shared_username})

        if response.status_code == 200:
            success = True
        else:
            success = False
    
    except requests.RequestException as e:
        print("Network error:", e)
        success = False

    return render_template('share.html', username=username, password=password, success=success)


@app.route('/event/<eventid>')
def view_event(eventid):
    try:
        # Get event details
        response = requests.get(f"http://event_service:5000/event/{eventid}")

        if response.status_code == 200:
            event_data = response.json()['event']
            # Get invite statuses for the event
            response_status = requests.get(f"{INVITE_SERVICE_URL}/get-invitation-status/{eventid}")
            if response_status.status_code == 200:
                status_data = response_status.json()['user_statuses']
                event_data.append(status_data)
                success = True
            else:
                success = False
                event_data = None

        else:
            success = False
            event_data = None
    except requests.RequestException as e:
        success = False
        event_data = None

    if success:
        event = event_data  # Use the fetched event details
    else:
        event = None  # No success, so don't fetch the data

    return render_template('event.html', username=username, password=password, event=event, success=success)

@app.route("/login", methods=['POST'])
def login():
    req_username, req_password = request.form['username'], request.form['password']

    url = "http://my_api:5000/login"
    payload = {'username': req_username, 'password': req_password}
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        success = True  # Login successful
    else:
        success = False

    save_to_session('success', success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/')

@app.route("/register", methods=['POST'])
def register():
    req_username, req_password = request.form['username'], request.form['password']

    url = "http://my_api:5000/register"
    payload = {'username': req_username, 'password': req_password}
    response = requests.post(url, data=payload)

    if response.status_code == 201:
        success = True
        calendar_payload = {
            'owner': req_username,
            'event_id_list': [],
            'calendar_share_list': []
        }
        calendar_response = requests.post(f"{CALENDAR_SERVICE_URL}/calendar", json=calendar_payload)
        if calendar_response.status_code != 201:
            success = False  # If adding to the calendar database fails, registration should fail
    else:
        success = False
    
    save_to_session('success', success)

    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/')

@app.route('/invites', methods=['GET'])
def invites():
    try:
        # Get pending invites for the current user
        response = requests.get(f"{INVITE_SERVICE_URL}/show-pending/{username}")
        if response.status_code == 200:
            event_ids = response.json().get('pending_event_ids', [])
        else:
            event_ids = []

        # Get event details for the pending invites
        event_details = []
        if event_ids:
            response = requests.post(f"{EVENT_SERVICE_URL}/events", json={'event_ids': event_ids})
            if response.status_code == 200:
                event_details = response.json().get('events', [])

        # Format event details
        my_invites = []
        for event in event_details:
            event_id = event['id']
            title = event['title']
            event_date = event['event_date']
            organizer = event['owner']
            event_type = event['event_type']
            my_invites.append((event_id, title, event_date, organizer, event_type.capitalize()))

        return render_template('invites.html', username=username, password=password, invites=my_invites)
    except requests.RequestException as e:
        # Handle network errors
        return render_template('error.html', message='Failed to communicate with the invite or event service')


@app.route('/invites', methods=['POST'])
def process_invite():
    eventId, status = request.json['event'], request.json['status']
    if status == "Participate":
        status = 'Participating'
    elif status == 'Maybe Participate':
        status = "Maybe Participating"
    else:
        status = "Not Participating"
    try:
        # Send a request to update invite status
        response = requests.post(f"{INVITE_SERVICE_URL}/change-status", json={
            'event_id': eventId,
            'answer': status,
            'user': username
        })
        if response.status_code == 200:
            if status in ["Participating", "Maybe Participating"]:
                # If the user is participating, add the event to their calendar
                add_response = requests.post(f"{CALENDAR_SERVICE_URL}/calendar/{username}/add", json={'event_id': eventId})
                add_response.raise_for_status()
                if add_response.status_code != 201:
                    return render_template('error.html', message='Failed to add event to calendar')
            return redirect(url_for('invites'))
        else:
            return render_template('error.html', message='Failed to process invite')
    except requests.RequestException as e:
        return render_template('error.html', message='Failed to communicate with the invite microservice')

@app.route("/logout")
def logout():
    global username, password

    # Clear the username and password to log out
    username = None
    password = None
    return redirect('/')
