from flask import Flask, render_template, request, jsonify, abort, redirect
from database.sql_handler import SQLHandler
from database.redis_handler import RedisHandler
from flask_cors import CORS
from webapi.storage_bucket import ManualStorageAPI
import random
import datetime
import os
import json
import requests

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
    server = create_database_connection()
    current_queue = server.get_query_result("SELECT url FROM archive_queue")
    server.close_connection()
    return render_template("index.html", queue=current_queue, queue_length=len(current_queue))

@app.route("/watch")
def watch_page():
    video_id = request.args.get('v')
    return redirect("https://patchwork.moekyun.me/watch?v=" + video_id)

@app.route("/api/channel/<channel_id>")
def api_get_channel_videos(channel_id):
    server = create_database_connection()
    page_number = int(request.args.get('page', 1))
    results_per_page = int(os.environ.get("RESULTS_PER_PAGE", 9))
    start_range = (page_number - 1) * results_per_page
    data = server.get_query_result("SELECT * FROM songs WHERE channel_id = %s ORDER BY upload_date DESC LIMIT %s, %s", (channel_id, start_range, results_per_page, ))
    total_num_results = server.get_query_result("SELECT COUNT(*) FROM songs WHERE channel_id = %s", (channel_id,))[0][0]
    pages = (total_num_results + results_per_page - 1) // results_per_page
    videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    server.close_connection()
    if not videos:
        return jsonify({"pages": 0, "results": []})
    return jsonify({"results": videos, "pages": pages})


@app.route("/api/status")
def get_service_status():
    if os.environ.get("USE_REDIS") == "True":
        redis_handler = RedisHandler()
        service_status = redis_handler.read_kv("service_status")
        if service_status:
            service_status = json.loads(service_status)  # Deserialize the data
            return jsonify(service_status)
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
    if os.environ.get("USE_REDIS") == "True":
        service_status = {"workers": workers}
        service_status_str = json.dumps(service_status)
        redis_handler.set_kv_data("service_status", service_status_str, 60)
    return jsonify({"workers": workers})

@app.route("/api/channel_name")
def get_channel_name():
    server = create_database_connection()
    channel_id = request.args.get('channel_id')
    query = """
    SELECT s.channel_name, c.description
    FROM songs s
    JOIN channels c ON s.channel_id = c.channel_id
    WHERE s.channel_id = %s
    ORDER BY s.upload_date DESC
    LIMIT 1
    """
    data = server.get_query_result(query, (channel_id,))
    if not data:
        query = "SELECT channel_name FROM songs WHERE channel_id = %s ORDER BY upload_date DESC LIMIT 1"
        data = server.get_query_result(query, (channel_id,))
        server.close_connection()
        if data:
            return jsonify({"channel_name": data[0][0], "description": ""})
        else:
            return jsonify({"error": "Channel ID does not exist"})
    server.close_connection()
    return jsonify({"channel_name": data[0][0], "description": data[0][1]})

@app.route("/api/search/results")
def api_search_query():
    server = create_database_connection()
    search_terms = request.args.get('q')
    page = request.args.get('page') if request.args.get('page') is not None else 1
    start_range = int(os.environ.get("RESULTS_PER_PAGE")) * (int(page) - 1)
    if not all(ord(char) < 128 for char in search_terms):
        data, result_count = server.search_row("songs","title", search_terms.split(), int(os.environ.get("RESULTS_PER_PAGE")), start_range)
    else:
        data, result_count = server.search_romanized_video("songs", "romanized_title", search_terms.split(), int(os.environ.get("RESULTS_PER_PAGE")), start_range)
    server.close_connection()
    max_pages = result_count // int(os.environ.get("RESULTS_PER_PAGE"))
    if max_pages == 0 and result_count != 0:
        max_pages = 1
    search_result = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    if len(search_result) == 0:
        return jsonify({"pages": 0, "results": []})
    return jsonify({"pages":max_pages,"results":search_result})

@app.route("/api/search/channel")
def api_search_channel():
    server = create_database_connection()
    search_terms = request.args.get('q')
    page = request.args.get('page') if request.args.get('page') is not None else 1
    start_range = int(os.environ.get("RESULTS_PER_PAGE_CHANNEL")) * (int(page) - 1)
    if not all(ord(char) < 128 for char in search_terms):
        data, result_count = server.search_channel_row("channels", search_terms.split(), int(os.environ.get("RESULTS_PER_PAGE_CHANNEL")), start_range)
    else:
        data, result_count = server.search_romanized_channel("channels", search_terms.split(), int(os.environ.get("RESULTS_PER_PAGE_CHANNEL")), start_range)
    server.close_connection()
    max_pages = result_count // int(os.environ.get("RESULTS_PER_PAGE_CHANNEL"))
    if max_pages == 0 and result_count != 0:
        max_pages = 1
    search_result = [{"channel_id": channel[0], "channel_name": channel[1], "description": channel[2]} for channel in data]
    if len(search_result) == 0:
        return jsonify({"pages": 0, "results": []})
    return jsonify({"pages":max_pages,"results":search_result})


@app.route("/api/video/<video_id>")
def api_get_video_data(video_id):
    server = create_database_connection()
    if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
        data = server.get_query_result("SELECT * FROM songs WHERE video_id = %s", (video_id,))
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
    if os.environ.get("USE_REDIS") == "True":
        redis_handler = RedisHandler()
        discover_cache = redis_handler.read_kv("discover_videos")
        if discover_cache:
            discover_cache = json.loads(discover_cache)  # Deserialize the data
            return jsonify(discover_cache)
    server = create_database_connection()
    count = request.args.get('count') if request.args.get('count') is not None else 6
    video_data = []
    for _ in range(int(count)):
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
    if os.environ.get("USE_REDIS") == "True":
        video_data_str = json.dumps(video_data)  # Serialize the data
        redis_handler.set_kv_data("discover_videos", video_data_str, 3600)
    return jsonify(video_data)

@app.route("/api/discover_channels")
def api_get_discover_channels():
    if os.environ.get("USE_REDIS") == "True":
        redis_handler = RedisHandler()
        discover_channels_cache = redis_handler.read_kv("discover_channels")
        if discover_channels_cache:
            discover_channels_cache = json.loads(discover_channels_cache)
            return jsonify(discover_channels_cache)
    server = create_database_connection()
    count = request.args.get('count') if request.args.get('count') is not None else 6
    channel_data = []
    for _ in range(int(count)):
        data = server.get_random_row(table_name="channels")
        dict_data = {}
        dict_data["channel_id"] = data[0][0]
        dict_data["channel_name"] = data[0][1]
        dict_data["romanized"] = data[0][2]
        channel_data.append(dict_data)
    server.close_connection()
    if os.environ.get("USE_REDIS") == "True":
        channel_data_str = json.dumps(channel_data)
        redis_handler.set_kv_data("discover_channels", channel_data_str, 3600)
    return jsonify(channel_data)


@app.route("/api/daily_featured_videos")
def api_get_daily_featured():
    if os.environ.get("USE_REDIS") == "True":
        redis_handler = RedisHandler()
        daily_feat_cache = redis_handler.read_kv("daily_featured")
        if daily_feat_cache:
            daily_feat_cache = json.loads(daily_feat_cache)  # Deserialize the data
            return jsonify(daily_feat_cache)
    server = create_database_connection()
    max_rows = server.get_query_result("SELECT COUNT(*) FROM songs")
    featured_indexes = pick_featured_videos(max_rows[0][0])
    featured_query = f"SELECT * FROM songs WHERE id IN ({featured_indexes[0]}, {featured_indexes[1]})"
    featured_data = server.get_query_result(featured_query)
    featured_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in featured_data]
    server.close_connection()
    if os.environ.get("USE_REDIS") == "True":
        featured_videos_str = json.dumps(featured_videos)  # Serialize the data
        redis_handler.set_kv_data("daily_featured", featured_videos_str, 86400)
    return jsonify(featured_videos)

@app.route("/api/recently_archived")
def api_get_recently_archived():
    server = create_database_connection()
    archived_data = server.get_query_result("SELECT * FROM songs ORDER BY id DESC LIMIT 6;" )
    recent_archived_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in archived_data]
    server.close_connection()
    return jsonify(recent_archived_videos)

@app.route("/api/popular")
def api_get_popular():
    """
    Gets the 6 videos that are most often accessed via the API
    """
    if os.environ.get("USE_REDIS") == "True":
        redis_handler = RedisHandler()
        daily_feat_cache = redis_handler.read_kv("popular")
        if daily_feat_cache:
            daily_feat_cache = json.loads(daily_feat_cache)  # Deserialize the data
            return jsonify(daily_feat_cache)
    server  = create_database_connection()
    popular_songs = server.get_query_result("""
        SELECT songs.video_id, songs.title, songs.channel_name, songs.channel_id, songs.upload_date, songs.description
        FROM songs
        JOIN views ON songs.video_id = views.video_id
        ORDER BY views.view_count DESC
        LIMIT 6;
    """)
    result = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in popular_songs]
    if os.environ.get("USE_REDIS") == "True":
        featured_videos_str = json.dumps(result)  # Serialize the data
        redis_handler.set_kv_data("popular", featured_videos_str, 86400)
    return result

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
    server = create_database_connection()
    data = server.get_query_result("SELECT * FROM files WHERE video_id = %s", (video_id,))
    file_size = 0
    file_ext = ".webm"
    if data:
        file_size = data[0][1]
        file_ext = data[0][2]
    if response.status_code == 404:
        if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
            data = server.get_query_result("SELECT * FROM songs WHERE video_id = %s", (video_id,))
            dict_data = {
                "video_id": data[0][0],
                "title": data[0][1],
                "channel": data[0][2],
                "channel_id": data[0][3],
                "upload_date": data[0][4],
                "description": data[0][5],
                "file_size": file_size,
                "file_size_units": "MB",
                "file_ext": file_ext
            }
            server.execute_query("""
                INSERT INTO views (video_id, view_count) VALUES (%s, 1)
                ON DUPLICATE KEY UPDATE view_count = view_count + 1"""
                , (video_id,))
            server.close_connection()
            return jsonify(dict_data)
        server.close_connection()
        return jsonify({"error": "Video ID does not exist"})
    elif response.status_code == 200:
        dict_data = response.json()
        dict_data["file_size"] = file_size
        dict_data["file_size_units"] = "MB"
        dict_data["file_ext"] = file_ext
        server.execute_query("""
            INSERT INTO views (video_id, view_count) VALUES (%s, 1)
            ON DUPLICATE KEY UPDATE view_count = view_count + 1"""
            , (video_id,))
        return jsonify(dict_data)
    else:
        return jsonify({"error": f"Unexpected status code: {response.status_code}"})

@app.route("/api/database/file_data/<video_id>")
def api_get_file_data(video_id):
    server = create_database_connection()
    if server.check_row_exists(table_name="files", column_name="video_id", value=video_id):
        data = server.get_query_result("SELECT * FROM files WHERE video_id = %s", (video_id, ))
        dict_data = {
            "video_id": data[0][0],
            "file_size": data[0][1],
            "file_size_units": "MB",
            "file_type": data[0][2]
        }
        server.close_connection()
        return jsonify(dict_data)

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
        storage_size, storage_size_units  = storage_api.get_storage_used()
        server.close_connection()
        return jsonify({"number_of_files": number_of_files, "storage_size": storage_size, "units": storage_size_units}), 200
    except Exception as e:
        print(e)
        return abort(500)

@app.route("/api/storage/delete", methods=["DELETE"])
def delete_video():
    """
    Endpoint for workers to delete an archived video
    """
    password = request.headers.get('X-AUTHENTICATION')
    video_id = request.form.get('videoId')
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
