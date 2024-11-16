import os
import pathlib
from flask import Flask, render_template, request, jsonify, abort, redirect, session
import mysql.connector
from mysql.connector import Error
from fetch import get_cloud_data  # Adjusted function to fetch and store cloud data
from fetch import generate_chatbot_responses  # Import the function from fetch.py
from google.oauth2 import id_token # type: ignore
from google_auth_oauthlib.flow import Flow # type: ignore
import google.auth.transport.requests # type: ignore
from chatbot import cloud_weather_chatbot

app = Flask(__name__)
app.secret_key = "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"  # Change this to a secure random string

# Google OAuth2 Configuration
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Allow HTTP traffic for local development
GOOGLE_CLIENT_ID = "973444997965-8qvk6df1psjqm0p3c4dq127u16g5t3nc.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "clientSecret.json")

flow = Flow.from_client_secrets_file(
    'clientSecret.json',  # Path to your downloaded client secret JSON file
    scopes=[
        'https://www.googleapis.com/auth/userinfo.profile', 
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ],
    redirect_uri='http://127.0.0.1:5000/index'  # Your redirect URI
)

# Google login required decorator
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

# Google Login Route
@app.route("/google-login")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

# Google OAuth callback route
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = request.session()
    token_request = google.auth.transport.requests.Request(session=request_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/index")


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'cloud_data'
}

def create_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None
    

@app.route('/')
def login():
    return render_template('login.html')

#################################
# Route for the main index page #
#################################
@app.route('/index')
def index():
    return render_template('index.html')  # Ensure you have an 'index.html' file in the templates folder

############################
# Handles the login process #
############################
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.json.get('username')
    password = request.json.get('password')

    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch user data
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['user_id']  # Store the user ID in the session
            
            # Check if the user has access to the "View User" button (Jea and password 777)
            view_user_permission = (username == "Jea" and password == "777")


            session['view_user_permission'] = view_user_permission

            return jsonify({
                'success': True,
                'message': 'Login successful',
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

            
##############################
# Handles the signup process #
##############################
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Insert the new user into the database
        cursor.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s)", (email, username, password))
        connection.commit()

        # Return the email and username for pre-filling the login form
        return jsonify({
            'success': True,
            'message': 'Signup successful',
            'email': email,
            'username': username
        }) 

    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


#########################################
# Get API data and store it in Database #
#########################################
@app.route('/get-stored-data', methods=['POST'])
def get_stored_data():
    data = request.get_json()
    latitude = float(data['latitude'])
    longitude = float(data['longitude'])

    print(f"[DEBUG] Received Latitude: {latitude}, Longitude: {longitude}")
    

    try:
        # Establish connection to the database
        connection = create_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection not available.'})

        cursor = connection.cursor(dictionary=True)

        # Fetch locations ID
        cursor.execute('''SELECT location_id FROM locations
                          WHERE latitude = CAST(%s AS DECIMAL(10, 7))
                          AND longitude = CAST(%s AS DECIMAL(10, 7))''',
                       (latitude, longitude))
        locations = cursor.fetchone()

        # If locations is not found, fetch cloud cover data from the API
        if not locations:
            print("[DEBUG] Locations not found. Fetching from API...")
            result = get_cloud_data(latitude, longitude)
            if not result:
                return jsonify({'success': False, 'message': 'Failed to fetch or store data from API.'})

            connection.commit()  # Save changes

            # Re-fetch the locations ID after inserting new data
            cursor.execute('''SELECT location_id FROM locations
                            WHERE latitude = CAST(%s AS DECIMAL(10, 7))
                            AND longitude = CAST(%s AS DECIMAL(10, 7))''',
                        (latitude, longitude))
            locations = cursor.fetchone()

        # Handle case where locations is not found
        if not locations:
            print("[ERROR] Locations insertion or retrieval failed.")
            return jsonify({'success': False, 'message': 'Locations insertion failed.'})

        location_id = locations['location_id']
        print(f"[DEBUG] Found Locations ID: {location_id}")

        # Fetch hourly cloud cover data
        cursor.execute('''SELECT time, cloud_cover_total
                          FROM hourly_cloud_cover
                          WHERE location_id = %s
                          ORDER BY time ASC''', (location_id,))
        hourly_data = cursor.fetchall()

        # Fetch current cloud cover data
        cursor.execute('''SELECT * FROM current_cloud_cover
                          WHERE location_id = %s
                          ORDER BY time DESC LIMIT 1''', (location_id,))
        current_data = cursor.fetchone()

        # Check if data exists
        if not hourly_data or not current_data:
            return jsonify({'success': False, 'message': 'No Cloud Cover data found for this locations.'})

        # Prepare response
        response = {
            'success': True,
            'hourly': {
                'time': [row['time'].strftime('%Y-%m-%d %H:%M') for row in hourly_data],
                'cloud_cover_total': [int(row['cloud_cover_total']) for row in hourly_data]
            },
            'current': {
                'time': current_data['time'].strftime('%Y-%m-%d %H:%M'),
                'cloud_cover_total': f"{int(current_data['cloud_cover_total'])} %",
                'cloud_cover_low': f"{int(current_data['cloud_cover_low'])} %",
                'cloud_cover_mid': f"{int(current_data['cloud_cover_mid'])} %",
                'cloud_cover_high': f"{int(current_data['cloud_cover_high'])} %",
                'visibility': f"{int(current_data['visibility'])} Meters"
            }
        }
        
    except Error as e:
        print(f"[ERROR] Database error: {e}")
        response = {'success': False, 'message': f'Database error: {str(e)}'}
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    print(f"[DEBUG] Response: {response}")
    return jsonify(response)


@app.route('/get-chatbot-response', methods=['GET'])
def get_chatbot_response():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    # Fetch cloud data from the database or an external source, for example
    # (This part is simplified for the purpose of the example)
    cloud_cover_total = [75]  # Example data
    cloud_cover_low = [50]    # Example data
    cloud_cover_mid = [25]    # Example data
    cloud_cover_high = [5]    # Example data
    visibility = [1000]       # Example data
    timestamps = ["2024-11-12T12:00"]  # Example timestamp

    # Call the generate_chatbot_responses function from fetch.py
    chatbot_responses = generate_chatbot_responses(
        latitude, longitude,
        cloud_cover_total,
        cloud_cover_low,
        cloud_cover_mid,
        cloud_cover_high,
        visibility,
        timestamps
    )

    # Return the chatbot responses
    return jsonify({"responses": chatbot_responses})



####################
# User Information #
####################
@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'GET':
        # Fetch user information for editing
        try:
            connection = create_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()

            if user:
                return render_template('edit_user.html', user=user), 200
            else:
                return jsonify({'success': False, 'message': 'User not found'}), 404

        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    elif request.method == 'POST':
        # Handle user account update
        data = request.json
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        # Validate inputs
        if not email or not username or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        try:
            connection = create_connection()
            cursor = connection.cursor()

            # Update user information in the database
            cursor.execute(
                "UPDATE users SET email=%s, username=%s, password=%s WHERE user_id=%s", 
                (email, username, password, user_id)
            )
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'No rows updated. User may not exist.'}), 404

            return jsonify({'success': True, 'message': 'Account updated successfully.'})

        except Error as e:
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

#################
## DELETE USER ##
#################
@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    logged_in_user_id = session.get('user_id')  # Retrieve logged-in user from session
    logged_in_username = session.get('username')  # Retrieve username from session
    
    # Logging session information for debugging
    print(f"Logged in user_id: {logged_in_user_id}")
    print(f"Logged in username: {logged_in_username}")

    if not logged_in_user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Retrieve logged-in user's password from the database
        cursor.execute("SELECT password FROM users WHERE user_id=%s", (logged_in_user_id,))
        logged_in_password = cursor.fetchone()[0]  # Fetch the password

        # Check if the logged-in user is deleting themselves,
        # or if the logged-in user is "Jea" or has password '777'
        if (logged_in_user_id == user_id or 
            logged_in_username == 'Jea' or 
            logged_in_password == '777'):
            
            cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
            connection.commit()

            return jsonify({'success': True, 'message': 'User deleted successfully.'})
        else:
            return jsonify({'success': False, 'message': 'Unauthorized to delete this user.'}), 403

    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


#######################
### USER INFOMATION ###
#######################
@app.route('/user-info', methods=['GET'])
def get_user_info():
    user_id = session.get('user_id')  # Assuming you use session to store logged-in user info

    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch user information from the database
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            return jsonify({'success': True, 'user': user}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/all-users')
def get_all_users():
    try:
        connection = create_connection()
        if connection is None:
            return "Error connecting to the database", 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        # Debug: Print the fetched users
        print("Fetched Users:", users)  # This will help you see if users are being retrieved

        return render_template('user.html', users=users)

    except Error as e:
        return f"Database error: {str(e)}", 500

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()



if __name__ == '__main__':
    app.run(debug=True)
