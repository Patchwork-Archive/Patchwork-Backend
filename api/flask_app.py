from flask import Flask, render_template, request, jsonify, abort, redirect
from flask_cors import CORS
import random
import datetime
import requests
import mysql.connector
from mysql.connector import Error, errorcode
from abc import ABC
import requests
import os
import dotenv

dotenv.load_dotenv()

class SQLHandler:
    def __init__(self):
        self.connection = self._create_server_connection()
        self._load_database(os.environ.get("DB_DATABASE").strip())
    
    def _create_server_connection(self) -> mysql.connector:
        connection = None
        try:
            connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_DATABASE"),
            user=os.environ.get("DB_USERNAME"),
            password=os.environ.get("DB_PASSWORD"),
            ssl_ca=os.environ.get("SSL_CERT"),
            use_pure=True
            )
        except Error as err:
            print(f"Error: '{err}'")
        if connection is None:
            print("Connection failed")
            exit(1)
        return connection

    def get_connection(self):
        return self.connection

    def _create_database(self, cursor: str, database_name: str):
        try:
            cursor.execute(
                f"CREATE DATABASE {database_name} DEFAULT CHARACTER SET 'utf8'")
        except Error as err:
            print(f"Failed creating database: {err}")
            exit(1)

    def _load_database(self, database_name: str):
        try:
            cursor = self.connection.cursor(buffered=True)
        except Error as err:
            print(f"Failed to load database: {err}")
            exit(1)
        try:
            print(f"Database {database_name} loaded successfully")
        except Error as err:
            print(f"Database {database_name} does not exist")
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                self._create_database(cursor, database_name)
                print(f"Database {database_name} created successfully")
                self.connection.database = database_name
            else:
                print(err)
                exit(1)

    def create_table(self, name: str, column: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"CREATE TABLE {name} ({column})")
            print(f"Table {name} created successfully")
        except Error as err:
            print(err)

    def insert_row(self, table_name: str, column: str, data: tuple):
        cursor = self.connection.cursor(buffered=True)
        try:
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table_name} ({column}) VALUES ({placeholders})"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Inserted:", data)
        except Error as err:
            print("Error inserting data")
            print(err)
            if err not in ("Duplicate entry", "Duplicate entry for key 'PRIMARY'"):
                return False
        return True

    def close_connection(self):
        if self.connection.is_connected():
            if hasattr(self, '_tunnel'):
                self._tunnel.stop()
            self.connection.close()
            print("MySQL connection is closed")


    def clear_table(self, name: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"DELETE FROM {name}")
            self.connection.commit()
            print("Table cleared successfully")
        except Error as err:
            print("Error clearing table")
            print(err)

    def reset_auto_increment(self, name: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"ALTER TABLE {name} AUTO_INCREMENT = 1")
            self.connection.commit()
            print("Table reset successfully")
        except Error as err:
            print("Error resetting table")
            print(err)

    def copy_rows_to_new_table(self, name: str, new_name: str, column: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(
                f"INSERT INTO {new_name} ({column}) SELECT {column} FROM {name}")
            cursor.execute(
                f"ALTER TABLE {new_name} MODIFY COLUMN id INT AUTO_INCREMENT")
            self.connection.commit()
            print("Rows copied successfully")
        except Error as err:
            print("Error copying rows")
            print(err)

    def drop_table(self, name: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"DROP TABLE {name}")
            self.connection.commit()
            print("Table dropped successfully")
        except Error as err:
            print("Error dropping table")
            print(err)
    
    def check_row_exists(self, table_name: str, column_name: str, value: str):
        """
        Checks if a row exists in a table
        """
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {column_name} = '{value}'")
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False
        except Error as err:
            print("Error checking row")
            print(err)

    def update_row(self, name: str, column_name: str, search_val: str, replace_col:str, new_value: str):
        """
        Updates a row in a table
        """
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"UPDATE {name} SET {replace_col} = '{new_value}' WHERE {column_name} = '{search_val}'")
            self.connection.commit()
            print("Row updated successfully")
        except Error as err:
            print("Error updating row")
            print(err)
    
    def execute_query(self, query: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error executing query")
            print(err)
    
    def get_query_result(self, query: str):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error executing query")
            print(err)

    def delete_row(self, name: str, column: str, data: tuple):
        cursor = self.connection.cursor()
        try:
            query = f"DELETE FROM {name} WHERE {column} = %s"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Deleted:", data)
        except Error as err:
            print("Error deleting data")
            print(err)
            return False
        return True
    
    def get_random_row(self,table_name: str, limit: int = 1):
        cursor = self.connection.cursor(buffered=True)
        try:
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY RAND() LIMIT {str(limit)}")
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error getting random row")
            print(err)
    
    def search_video_row(self, table_name: str, keywords: list, limit: int = 1, offset: int = 0):
        cursor = self.connection.cursor(buffered=True)
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        keyword_conditions = [] 

        for keyword in keywords:
            keyword_condition = f"LOWER(title) LIKE %s"
            formatted_keyword = f"%{keyword.lower()}%"  
            keyword_conditions.append((keyword_condition, formatted_keyword))  
        if keyword_conditions:
            query += " AND " + " AND ".join([condition[0] for condition in keyword_conditions])
        count_query = query
        query += " LIMIT %s OFFSET %s"

        try:
            cursor.execute(count_query, ([condition[1] for condition in keyword_conditions]))
            result_count = len(cursor.fetchall())
            cursor.execute(query, ([condition[1] for condition in keyword_conditions] + [limit, offset]))
            result = cursor.fetchall()
            return result, result_count
        except Error as err:
            print("Error searching video row")
            print(err)



class WebAPI():
    """
    General class for interacting with web APIs
    """

    def __init__(self, api_key: str, base_url: str, headers: dict) -> None:
        self.api_key = api_key
        self._base_url = base_url
        self._headers = headers

    def _get_url(self, query: str) -> dict:
        """
        Downloads the URL and returns the result as a dict
        param:
            query: str - the query to be appended to the base URL
        """
        response = requests.get(query, headers=self._headers)
        json_data = response.json()
        return json_data


class StorageAPI(ABC, WebAPI):
    """
    The data for this use case is stored on CloudFlare R2 Storage
    However so long as all methods are implemented the class can be re-written to use any other API
    """
    def __init__(self, api_key: str, base_url: str, headers:dict) -> None:
        super().__init__(api_key, base_url, headers)
    
    def get_storage_used(self) -> tuple[int,str]:
        """
        Returns the amount of storage used and the unit of measurement
        """
        pass

    def get_number_of_files(self) -> int:
        """
        Returns the number of files stored
        """
        pass
    
class ManualStorageAPI(StorageAPI):
    def __init__(self, server: SQLHandler) -> None:
        super().__init__(None, None, None)
        self.server = server

    def get_storage_used(self) -> tuple[int,str]:
        """
        Returns the amount of storage used and the unit of measurement
        """
        print("Getting storage used")
        if not self.server.check_row_exists("kv", "DATA", "video_bucket_size"):
            print("Inserting row")
            self.server.insert_row("kv", "DATA, REFERENCE", ("video_bucket_size", "0"))
        print(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_size'"))
        storage_used = int(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_size'")[0][0])

        return storage_used

    def get_number_of_files(self) -> int:
        """
        Returns the number of files stored
        """
        if not self.server.check_row_exists("kv", "DATA", "video_bucket_count"):
            self.server.insert_row("kv", "DATA, REFERENCE", ("video_bucket_count", "0"))
        obj_count = int(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_count'")[0][0])
        print(obj_count)
        return obj_count



app = Flask(__name__)
CORS(app)
current_radio_data = None


def create_database_connection():
    return SQLHandler()


def pick_featured_videos(max_videos: int):
    today = datetime.date.today()
    date_integer = int(today.strftime("%Y%m%d"))
    random.seed(date_integer)
    n1 = random.randint(1, max_videos)
    n2 = random.randint(1, max_videos)
    return n1, n2


@app.route("/")
def landing_page():
    return render_template("index.html")

@app.route("/watch")
def watch_page():
    video_id = request.args.get('v')
    return redirect("https://patchwork.moekyun.me/watch?v=" + video_id)

@app.route("/api/channel/<channel_id>")
def api_get_channel_videos(channel_id):
    server = create_database_connection()
    page_number = request.args.get('page') if request.args.get('page') is not None else 0
    start_range = (int(page_number) - 1) * 9
    end_range = start_range + 9
    data = server.get_query_result(f"SELECT * FROM songs WHERE channel_id = '{channel_id}' ORDER BY upload_date DESC LIMIT {str(start_range)}, {str(end_range)}")
    total_num_results = server.get_query_result(f"SELECT COUNT(*) FROM songs WHERE channel_id = '{channel_id}'")[0][0]
    pages = total_num_results // 9
    if pages == 0 and total_num_results != 0:
        pages = 1
    videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    if len(videos) == 0:
        return render_template("search_no_result.html", search_terms="No videos found")
    server.close_connection()
    return jsonify({"results": videos, "pages": pages})


@app.route("/api/status")
def get_service_status():
    server = create_database_connection()
    worker_data = server.get_query_result("SELECT * FROM worker_status")
    workers = []
    for worker in worker_data:
        worker_dict = {}
        worker_dict["name"] = worker[1]
        worker_dict["status"] = worker[3]
        worker_dict["timestamp"] = worker[4]
        workers.append(worker_dict)
    server.close_connection()
    return jsonify({"workers": workers})


@app.route("/api/channel_name")
def get_channel_name():
    server = create_database_connection()
    channel_id = request.args.get('channel_id')
    data = server.get_query_result(f"SELECT channel_name FROM songs WHERE channel_id = '{channel_id}' LIMIT 1")
    server.close_connection()
    if len(data) == 0:
        return jsonify({"error": "Channel ID does not exist"})
    return jsonify({"channel_name": data[0][0]})

@app.route("/api/search/results")
def api_search_query():
    server = create_database_connection()
    search_terms = request.args.get('q')
    page = request.args.get('page') if request.args.get('page') is not None else 1
    start_range = int(os.environ.get("RESULTS_PER_PAGE")) * (int(page) - 1)
    data, result_count = server.search_video_row("songs", search_terms.split(), int(os.environ.get("RESULTS_PER_PAGE")), start_range)
    server.close_connection()
    max_pages = result_count // int(os.environ.get("RESULTS_PER_PAGE"))
    if max_pages == 0 and result_count != 0:
        max_pages = 1
    search_result = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    if len(search_result) == 0:
        return jsonify({"pages": 0, "results": []})
    return jsonify({"pages":max_pages,"results":search_result})

@app.route("/api/video/<video_id>")
def api_get_video_data(video_id):
    server = create_database_connection()
    if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
        data = server.get_query_result(f"SELECT * FROM songs WHERE video_id = '{video_id}'")
        dict_data = {}
        dict_data["video_id"] = data[0][0]
        dict_data["title"] = data[0][1]
        dict_data["channel_name"] = data[0][2]
        dict_data["channel_id"] = data[0][3]
        dict_data["upload_date"] = data[0][4]
        dict_data["description"] = data[0][5]
        return dict_data
    server.close_connection()
    return {"error": "Video ID does not exist"}

@app.route("/api/random_video")
def api_get_random_video():
    server = create_database_connection()
    data = server.get_random_row(table_name="songs")
    dict_data = {}
    dict_data["video_id"] = data[0][0]
    dict_data["title"] = data[0][1]
    dict_data["channel_name"] = data[0][2]
    dict_data["channel_id"] = data[0][3]
    dict_data["upload_date"] = data[0][4]
    dict_data["description"] = data[0][5]
    server.close_connection()
    return dict_data

@app.route("/api/discover_videos")
def api_get_discover_video():
    server = create_database_connection()
    count = request.args.get('count') if request.args.get('count') is not None else 6
    video_data = []
    for i in range(int(count)):
        data = server.get_random_row(table_name="songs")
        dict_data = {}
        dict_data["video_id"] = data[0][0]
        dict_data["title"] = data[0][1]
        dict_data["channel_name"] = data[0][2]
        dict_data["channel_id"] = data[0][3]
        dict_data["upload_date"] = data[0][4]
        dict_data["description"] = data[0][5]
        video_data.append(dict_data)
    server.close_connection()
    return jsonify(video_data)


@app.route("/api/daily_featured_videos")
def api_get_daily_featured():
    server = create_database_connection()
    max_rows = server.get_query_result("SELECT COUNT(*) FROM songs")
    featured_indexes = pick_featured_videos(max_rows[0][0])
    featured_query = f"SELECT * FROM songs WHERE id IN ({featured_indexes[0]}, {featured_indexes[1]})"
    featured_data = server.get_query_result(featured_query)
    featured_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in featured_data]
    server.close_connection()
    return jsonify(featured_videos)

@app.route("/api/recently_archived")
def api_get_recently_archived():
    server = create_database_connection()
    archived_data = server.get_query_result("SELECT * FROM songs ORDER BY id DESC LIMIT 6;" )
    recent_archived_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in archived_data]
    server.close_connection()
    return jsonify(recent_archived_videos)

@app.route("/api/database/video_data/<video_id>")
def api_get_video_data_from_database(video_id):
    """
    Used as a fallback for when video data cannot be retrieved from .info.json
    Emulated the format of the data from the .info.json file generated by yt-dlp
    """
    headers = {
        'User-Agent': 'python-requests/2.31.0',
        'Content-Type': 'pythonanywhere'
    }
    response = requests.get(f"https://content.pinapelz.com/file/vtuber-rabbit-hole-archive/VTuber+Covers+Archive/metadata/{video_id}.info.json", headers=headers)

    if response.status_code == 404:
        server = create_database_connection()
        if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
            data = server.get_query_result(f"SELECT * FROM songs WHERE video_id = '{video_id}'")
            dict_data = {
                "video_id": data[0][0],
                "title": data[0][1],
                "channel": data[0][2],
                "channel_id": data[0][3],
                "upload_date": data[0][4],
                "description": data[0][5]
            }
            server.close_connection()
            return jsonify(dict_data)
        server.close_connection()
        return jsonify({"error": "Video ID does not exist"})
    elif response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": f"Unexpected status code: {response.status_code}"})
    
@app.route("/api/stats")
def api_get_stats():
    server = create_database_connection()
    song_count = server.get_query_result("SELECT COUNT(video_id) FROM songs")
    return jsonify({"song_count": song_count[0][0]})

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "Page not found"}), 404

@app.route("/api/worker/queue", methods=["POST"])
def archive_url():
    """
    Endpoint for queueing a video to workers
    """
    password = request.headers.get('X-AUTHENTICATION')
    if password is None:
        abort(401)
    server = create_database_connection()
    try:
        if not server.check_row_exists("archive_queue_auth", "token", password):
            abort(401)
    except:
        abort(401)
    url = request.form.get('url')
    mode = int(request.form.get('mode'))

    if server.check_row_exists("archive_queue", "url", url):
        server.close_connection()
        return "Already queued"
    server.insert_row("archive_queue", "url, mode", (url, mode,))
    server.insert_row("archive_log", "url, user, status, timestamp", (url, password, "Queued", datetime.datetime.now()))
    server.close_connection()
    return "OK", 200


def get_next_video_in_queue():
    """
    Gets the next video in the queue
    """
    server = create_database_connection()
    try:
        data = server.get_query_result("SELECT url, mode FROM archive_queue ORDER BY id LIMIT 1;")[0]
        if data is None:
            return None, None
        next_video, mode = data[0], data[1]
    except IndexError:
        server.close_connection()
        return None
    server.delete_row("archive_queue", "url", (next_video,))
    server.close_connection()
    return next_video, mode


@app.route("/api/worker/next", methods=["GET"])
def get_next_in_queue():
    """
    Endpoint for workers to get the next video in the queue
    """
    password = request.headers.get('X-AUTHENTICATION')
    server = create_database_connection()
    try:
        if not server.check_row_exists("archive_worker_auth", "token", password):
            abort(401)
    except:
        abort(401)
    next_video, mode = get_next_video_in_queue()
    if next_video is None:
        server.close_connection()
        return "No videos in queue", 204
    server.update_row("archive_log", "url", next_video, "status", "Processed",)
    server.close_connection()
    return jsonify({"next_video": next_video, "mode": mode})

@app.route("/api/worker/heartbeat", methods=["POST"])
def worker_heartbeat():
    """
    Endpoint for workers to send a heartbeat
    """
    password = request.headers.get('X-AUTHENTICATION')
    name = request.form.get('name')
    status = request.form.get('status')
    print(name, status)
    server = create_database_connection()
    try:
        if not server.check_row_exists("archive_worker_auth", "token", password):
            abort(401)
    except:
        abort(401)
    
    if not server.check_row_exists("worker_status", "token", password):
        server.insert_row("worker_status", "name, token, status, timestamp", (name, password, status, datetime.datetime.now()))
    else:
        server.update_row("worker_status", "token", password, "name", name)
        server.update_row("worker_status", "token", password, "status", status)
        server.update_row("worker_status", "token", password, "timestamp", datetime.datetime.now())
    server.close_connection()
    return "OK", 200

@app.route("/api/database/status", methods=["GET"])
def get_database_status():
    """
    Endpoint for workers to get the database status
    """
    try:
        server = create_database_connection()
        server.close_connection()
        return "OK", 200
    except Exception as e:
        return abort(500)

@app.route("/api/storage/status", methods=["GET"])
def get_storage_status():
    """
    Endpoint for workers to get the storage status
    Number of videos and storage size
    """
    try:
        server = create_database_connection()
        storage_api = ManualStorageAPI(server)
        number_of_files = int(server.get_query_result("SELECT COUNT(*) FROM songs")[0][0])
        storage_size = str(round(int(storage_api.get_storage_used())/ (1024 **3), 2))
        server.close_connection()
        return jsonify({"number_of_files": number_of_files, "storage_size": storage_size}), 200
    except Exception as e:
        return abort(500)

@app.route("/api/storage/delete", methods=["POST"])
def delete_video():
    """
    Endpoint for workers to delete an archived video
    """
    password = request.headers.get('X-AUTHENTICATION')
    video_id = request.form.get('video_id')
    server = create_database_connection()
    try:
        if not server.check_row_exists("archive_worker_auth", "token", password):
            abort(401)
    except:
        abort(401)
    if server.check_row_exists("songs", "video_id", video_id):
        server.delete_row("songs", "video_id", (video_id,))
    try:
        server.insert_row("archive_queue", "url, mode", (video_id, 2,))
    except:
        abort(401)
    server.close_connection()

if __name__ == "__main__":
    app.run(debug=True)
