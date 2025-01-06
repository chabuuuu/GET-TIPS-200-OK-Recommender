import csv
import redis
import tensorflow as tf
import pandas as pd
import numpy as np
from datetime import datetime
from urllib.parse import urlparse
import json  # Import json to handle string to JSON conversion
import os
from psycopg2 import pool


from dotenv import load_dotenv
load_dotenv()
# Define interaction types and weights
INTERACTION_WEIGHTS = {
    "click": 1.0,
    "view": 0.8,
    "scroll": 0.5,
    "share": 1.2,
    "comment": 1.5
}

class PostLoad:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_csv()
        # Redis Connection
        redis_url = os.getenv('REDIS_URL')

        # Parse the Redis URL to get the connection parameters
        parsed_url = urlparse(redis_url)
        redis_client = redis.StrictRedis(
            host=parsed_url.hostname,
            port=parsed_url.port,
            username=parsed_url.username,
            password=parsed_url.password,
            ssl=True,
            decode_responses=True
        )
        self.redis_client = redis_client

    def _connect_db(self):
        """Get a connection from the database connection pool."""
        return self.db_connection.get_connection()
    

    def _read_csv(self):
        data = {}
        with open(self.file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data[row['id']] = row['title']
        return data

    def get_title_by_id(self, post_id):
        return self.data.get(post_id.lower(), "ID not found")


    # Preprocess data to include weights and normalized features
    def preprocess_session_data(self, session_data, session_id):
        interactions = []
        for record in session_data:
            interaction_type = record.get("type")
            post_id = record.get("post_id")
            timestamp = record.get("timestamp")
            weight = INTERACTION_WEIGHTS.get(interaction_type, 0)

            if interaction_type == "view":
                view_time = record.get("viewTime", 0)
                weight *= min(view_time / 30, 1)  # Normalize viewTime, assuming 30s max
            elif interaction_type == "scroll":
                scroll_depth = record.get("scrollDepth", 0)
                weight *= min(scroll_depth / 100, 1)  # Normalize scrollDepth

            # Append interaction along with timestamp for sorting later
            interactions.append({
                "session_id": session_id,
                "post_id": post_id,
                "weight": weight,
                "timestamp": timestamp
            })

        # Convert the list of interactions to a DataFrame
        return pd.DataFrame(interactions)

    # Fetch all session data from Redis and process as JSON
    def get_all_sessions_data(self):
        all_sessions_data = []
        
        # Get all keys starting with TRACKING:
        keys = self.redis_client.keys("TRACKING:*")
        
        for session_key in keys:
            session_data_str = self.redis_client.get(session_key)
            if session_data_str:
                # Convert the string to JSON (list of records)
                session_data = json.loads(session_data_str)  # Assuming the data is a JSON string
                session_data = sorted(session_data, key=lambda x: datetime.strptime(x['timestamp'].replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f"))
                session_id = session_key.split(":")[-1]  # Extract session_id from key
                session_df = self.preprocess_session_data(session_data, session_id)
                all_sessions_data.append(session_df)
        
        # Combine all session DataFrames into one
        if all_sessions_data:
            return pd.concat(all_sessions_data, ignore_index=True)
        else:
            return pd.DataFrame()  # Return empty DataFrame if no session data
        
    def save_data_to_redis(self, key, values):
        """Save a list of strings as a value in Redis with the specified key."""
        if isinstance(values, list) and all(isinstance(value, str) for value in values):
            # Convert the list of strings to a JSON string
            json_data = json.dumps(values)
            # Save to Redis with TTL of 3 days (259200 seconds)
            self.redis_client.set("RECOMMEND:" + key, json_data, ex=259200)  
            print(f"Data saved to Redis with key: {key}")
        else:
            raise ValueError("The 'values' must be a list of strings.")
        
if __name__ == "__main__":
    filePath="/home/haphuthinh/Workplace/School_project/do-an-1/Get-tips-200-ok-recommend/post.csv"
    postload = PostLoad(filePath)
    print(postload.get_all_sessions_data())