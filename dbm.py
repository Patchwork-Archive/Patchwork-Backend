"""
Database Manager Module to be executed seperately for adding and removing auth tokens
"""
from sql_handler import SQLHandler
import fileutil
import argparse

if fileutil.check_file_exists("config.ini"):
    CONFIG = fileutil.read_config("config.ini")
else:
    CONFIG = fileutil.read_config("/home/pinapelz/cover_viewer/config.ini")

def create_database_connection():
    hostname = CONFIG.get("database", "host")
    user = CONFIG.get("database", "user")
    password = CONFIG.get("database", "password")
    database = CONFIG.get("database", "database")
    ssh_host = CONFIG.get("database", "ssh_host")
    ssh_username = CONFIG.get("database", "ssh_username")
    ssh_password = CONFIG.get("database", "ssh_password")
    remote_bind = CONFIG.get("database", "remote_bind")
    if ssh_host.strip() == "" or ssh_username.strip() == "" or ssh_password.strip() == "":
        return SQLHandler(hostname, user, password, database)
    return SQLHandler(hostname, user, password, database, ssh_host, ssh_username, ssh_password, remote_bind)

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
    server.create_table("archive_queue", "id INTEGER PRIMARY KEY AUTO_INCREMENT, url TEXT")
    server.create_table("archive_queue_auth", "id INTEGER PRIMARY KEY AUTO_INCREMENT, token TEXT")
    server.create_table("archive_worker_auth", "id INTEGER PRIMARY KEY AUTO_INCREMENT, token TEXT")
    server.create_table("archive_log", "id INTEGER PRIMARY KEY AUTO_INCREMENT, url TEXT, user TEXT, status TEXT, timestamp TEXT")
    server.create_table("worker_status", "id INTEGER PRIMARY KEY AUTO_INCREMENT, name TEXT, token TEXT, status TEXT, timestamp TEXT")
    
    if args.addqueuetoken is not None:
        print("Adding queue token...")
        server.insert_row("archive_queue_auth", "token", (args.addqueuetoken,))
    
    if args.addworkertoken is not None:
        print("Adding worker token...")
        server.insert_row("archive_worker_auth", "token", (args.addworkertoken,))


if __name__ == "__main__":
    main()
