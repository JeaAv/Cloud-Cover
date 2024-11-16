import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def get_cloud_data(latitude, longitude):
    url = f'https://barmmdrr.com/connect/gweather_api?latitude={latitude}&longitude={longitude}&hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility&timezone=Asia%2FSingapore'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(f"[DEBUG] API Response Data: {data}")

        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='cloud_data'
            )
            cursor = connection.cursor()

            # Insert location if not present
            insert_location_query = '''
            INSERT INTO locations (latitude, longitude) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE location_id=LAST_INSERT_ID(location_id);
            '''
            cursor.execute(insert_location_query, (latitude, longitude))

            # Fetch the location_id
            cursor.execute('''SELECT location_id FROM locations WHERE latitude = %s AND longitude = %s''', (latitude, longitude))
            location_id = cursor.fetchone()
            if location_id:
                location_id = location_id[0]
            else:
                print("[ERROR] Location ID retrieval failed after insertion.")
                return False

            # Store hourly cloud cover data
            hourly_data = data.get('hourly', {})
            timestamps = hourly_data.get('time', [])
            cloud_cover_total = hourly_data.get('cloud_cover', [])
            cloud_cover_low = hourly_data.get('cloud_cover_low', [])
            cloud_cover_mid = hourly_data.get('cloud_cover_mid', [])
            cloud_cover_high = hourly_data.get('cloud_cover_high', [])
            visibility = hourly_data.get('visibility', [])

            if not timestamps or not cloud_cover_total:
                print("[ERROR] Insufficient hourly data found in the API response.")
                return False

            try:
                for i in range(len(timestamps)):
                    timestamp = datetime.strptime(timestamps[i], '%Y-%m-%dT%H:%M')
                    total_cover = cloud_cover_total[i]
                    low_cover = cloud_cover_low[i] if i < len(cloud_cover_low) else None
                    mid_cover = cloud_cover_mid[i] if i < len(cloud_cover_mid) else None
                    high_cover = cloud_cover_high[i] if i < len(cloud_cover_high) else None
                    visibility_val = visibility[i] if i < len(visibility) else None

                    insert_hourly_query = '''
                    INSERT INTO hourly_cloud_cover (location_id, time, cloud_cover_total, cloud_cover_low, cloud_cover_mid, cloud_cover_high, visibility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                    cursor.execute(insert_hourly_query, (location_id, timestamp, total_cover, low_cover, mid_cover, high_cover, visibility_val))

                print(f"[DEBUG] Successfully inserted hourly cloud cover data for location ID {location_id}.")
            except Error as e:
                print(f"[ERROR] Error inserting hourly cloud cover data: {e}")
                return False

            # Store current cloud cover data
            current_total_cover = cloud_cover_total[0] if cloud_cover_total else None
            current_low_cover = cloud_cover_low[0] if cloud_cover_low else None
            current_mid_cover = cloud_cover_mid[0] if cloud_cover_mid else None
            current_high_cover = cloud_cover_high[0] if cloud_cover_high else None
            current_visibility = visibility[0] if visibility else None

            insert_current_query = '''
            INSERT INTO current_cloud_cover (location_id, time, cloud_cover_total, cloud_cover_low, cloud_cover_mid, cloud_cover_high, visibility)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_current_query, (location_id, timestamps[0], current_total_cover, current_low_cover, current_mid_cover, current_high_cover, current_visibility))

            connection.commit()

            # Adding chatbot responses (this is new)
            chatbot_responses = generate_chatbot_responses(latitude, longitude, cloud_cover_total, cloud_cover_low, cloud_cover_mid, cloud_cover_high, visibility, timestamps)

            print("[DEBUG] Chatbot Responses Generated:")
            for response in chatbot_responses:
                print(response)

            return True

        except Error as e:
            print(f"[ERROR] Database error: {e}")
            return False

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        print(f"[ERROR] API request failed with status: {response.status_code}")
        return False

def generate_chatbot_responses(latitude, longitude, cloud_cover_total, cloud_cover_low, cloud_cover_mid, cloud_cover_high, visibility, timestamps):
    # Generate chatbot responses based on hourly data
    chatbot_responses = []

    # First, add a summary of the current weather (only the first result)
    if cloud_cover_total:
        current_message = f"Currently, the cloud cover at Latitude {latitude} and Longitude {longitude} is {cloud_cover_total[0]}%.\n"
        current_message += f"High Clouds: {cloud_cover_high[0]}%, Mid Clouds: {cloud_cover_mid[0]}%, Low Clouds: {cloud_cover_low[0]}%, Visibility: {visibility[0]} meters."
        chatbot_responses.append(current_message)

    return chatbot_responses
