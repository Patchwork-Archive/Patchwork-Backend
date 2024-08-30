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
    print("Note: This script onyl works after applying the schema.sql to your DB")
    if args.addqueuetoken is not None:
        print("Adding queue token...")
        server.insert_row("archive_queue_auth", "token", (args.addqueuetoken,))
    
    if args.addworkertoken is not None:
        print("Adding worker token...")
        server.insert_row("archive_worker_auth", "token", (args.addworkertoken,))

if __name__ == "__main__":
    main()
