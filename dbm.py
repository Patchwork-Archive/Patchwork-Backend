"""
Database Manager Module to be executed separately for adding and removing auth tokens
"""
from database.sql_handler import SQLHandler
import argparse

def create_database_connection():
    return SQLHandler()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--addqueuetoken', type=str, help='Add a queue token for contributing to archival queue')
    parser.add_argument('--addworkertoken', type=str, help='Add a worker token for processing archival queue')
    print("Attempting to create database connection...")
    try:
        server = create_database_connection()
    except Exception as e:
        print("Failed to create database connection. Error: {}".format(e))
        return
    print("Database connection established.\n")
    args = parser.parse_args()
    server.create_table("archive_log", "id INTEGER PRIMARY KEY AUTO_INCREMENT, url TEXT NOT NULL, user VARCHAR(128) NOT NULL, status TEXT NOT NULL, timestamp TEXT")
    server.create_table("archive_queue", "id INTEGER PRIMARY KEY AUTO_INCREMENT, url TEXT, mode INTEGER")
    server.create_table("archive_queue_auth", "id INTEGER PRIMARY KEY AUTO_INCREMENT, token VARCHAR(128)")
    server.create_table("archive_worker_auth", "id INTEGER PRIMARY KEY AUTO_INCREMENT, token VARCHAR(128) NOT NULL")
    server.create_table("worker_status", "id INTEGER PRIMARY KEY AUTO_INCREMENT, name TEXT, token VARCHAR(128), status TEXT, timestamp TEXT")
    server.create_table("kv", "DATA VARCHAR(255) NOT NULL PRIMARY KEY, REFERENCE VARCHAR(255)")
    server.create_table("songs", "video_id VARCHAR(255) NOT NULL, title TEXT NOT NULL, channel_name TEXT NOT NULL, channel_id VARCHAR(255) NOT NULL, upload_date TEXT NOT NULL, description TEXT NOT NULL, id INTEGER PRIMARY KEY AUTO_INCREMENT")
    server.create_table("romanized", "id INTEGER PRIMARY KEY AUTO_INCREMENT, video_id VARCHAR(255) NOT NULL, romanized_title TEXT NOT NULL")
    server.create_table("channels", "channel_id VARCHAR(255) NOT NULL PRIMARY KEY, channel_name TEXT NOT NULL, romanized_name TEXT, description TEXT")

    # TODO: Add foreign key constraints
    """
    server.add_constraint("channels", "FOREIGN KEY (channel_id) REFERENCES songs (channel_id)")
    server.add_constraint("romanized", "FOREIGN KEY (video_id) REFERENCES songs (video_id) ON DELETE CASCADE")
    server.add_constraint("worker_status", "FOREIGN KEY (token) REFERENCES archive_worker_auth (token)")
    """

    # TODO: Add indexes
    """
    server.create_index("archive_worker_auth", "token")
    server.create_index("songs", "channel_id")
    server.create_index("songs", "video_id")
    """

    if args.addqueuetoken is not None:
        print("Adding queue token...")
        server.insert_row("archive_queue_auth", "token", (args.addqueuetoken,))
    
    if args.addworkertoken is not None:
        print("Adding worker token...")
        server.insert_row("archive_worker_auth", "token", (args.addworkertoken,))

if __name__ == "__main__":
    main()
