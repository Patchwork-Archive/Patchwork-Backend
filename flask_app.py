from flask import Flask, render_template, request, jsonify, abort
from database.sql_handler import SQLHandler
from flask_cors import CORS
from webapi.manual_storage_data import ManualStorageAPI
import random
import datetime
import re
import utils.fileutil as fileutil

app = Flask(__name__)
CORS(app)
current_radio_data = None

if fileutil.check_file_exists("config.ini"):
    CONFIG = fileutil.read_config("config.ini")
    SITE_CONFIG = fileutil.read_site_config("site_config.json")
else:
    CONFIG = fileutil.read_config("/home/pinapelz/cover_viewer/config.ini")
    SITE_CONFIG = fileutil.read_site_config("/home/pinapelz/cover_viewer/site_config.json")


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


def pick_featured_videos(max_videos: int):
    today = datetime.date.today()
    date_integer = int(today.strftime("%Y%m%d"))
    random.seed(date_integer)
    n1 = random.randint(1, max_videos)
    n2 = random.randint(1, max_videos)
    return n1, n2

@app.route("/radio")
def random_video_player():
    return render_template(
        "radio.html",
        domain=SITE_CONFIG["domain"],
        cdn=SITE_CONFIG["cdn"],
        thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
        )

@app.route("/")
def landing_page():
    server = create_database_connection()
    server.create_table("kv", "DATA VARCHAR(255) PRIMARY KEY, REFERENCE VARCHAR(255)")
    storage_api = ManualStorageAPI(CONFIG["storage"]["api_token"], CONFIG["storage"]["accountID"], CONFIG["storage"]["bucket_name"], server)
    video_count = request.args.get('count') if request.args.get('count') is not None else 6
    data = server.get_random_row(table_name="songs", limit=video_count)
    videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    archived_data = server.get_query_result("SELECT * FROM songs ORDER BY id DESC LIMIT 6;" )
    recent_archived_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in archived_data]
    max_rows = server.get_query_result("SELECT COUNT(*) FROM songs")
    featured_indexes = pick_featured_videos(max_rows[0][0])
    featured_query = f"SELECT * FROM songs WHERE id IN ({featured_indexes[0]}, {featured_indexes[1]})"
    featured_data = server.get_query_result(featured_query)
    featured_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in featured_data]
    try:
        number_of_files = int(server.get_query_result("SELECT COUNT(*) FROM songs")[0][0])
        storage_size = str(round(int(storage_api.get_storage_used())/ (1024 **3), 2))
    except:
        number_of_files = "some number"
        storage_size = "a lot"
    server.close_connection()
    return render_template("landing.html", 
                            videos=videos,
                            domain=SITE_CONFIG["domain"],
                            thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
                            recent_archived_videos=recent_archived_videos,
                            featured_videos=featured_videos,
                            archived_videos_count=f"{number_of_files:,}" if isinstance(number_of_files, int) and number_of_files >= 10000 else str(number_of_files), #　Pretty print the number of files
                            archive_size=storage_size,
                           )

@app.route("/watch")
def watch_video():
    server = create_database_connection()
    video_id = request.args.get('v')
    if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
        video_data = server.get_query_result(f"SELECT * FROM songs WHERE video_id = '{video_id}'")
        discover_data = server.get_random_row(table_name="songs", limit=5)
        discover_videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in discover_data]
        server.close_connection()
        description = re.sub(r'\\n', '<br>', video_data[0][5])
        return render_template("video.html",
                                discover_videos = discover_videos,
                                video_id=video_data[0][0],
                                domain=SITE_CONFIG["domain"],
                                cdn=SITE_CONFIG["cdn"],
                                thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
                                metadata_domain=SITE_CONFIG["metadata_domain"],
                                video_title = video_data[0][1],
                                channel_name = video_data[0][2],
                                upload_date = video_data[0][4],
                                channel_id = video_data[0][3],
                                description = description,
                               )
    server.close_connection()
    return render_template("404.html")

@app.route("/results")
def search_query():
    server = create_database_connection()
    search_terms = request.args.get('search_query')
    page = request.args.get('page') if request.args.get('page') is not None else 1
    start_range = int(SITE_CONFIG["search_results_per_page"]) * (int(page) - 1)
    data = server.search_video_row("songs", search_terms.split(), int(SITE_CONFIG["search_results_per_page"]), start_range)
    server.close_connection()
    search_result = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    if len(search_result) == 0:
        return render_template("search_no_result.html", search_terms=search_terms)
    return render_template("search.html", 
                           search_result=search_result,
                           search_terms = search_terms,
                           thumbnails_domain=SITE_CONFIG["thumbnails_domain"],)

@app.route("/channel/<channel_id>")
def channel_page(channel_id):
    server = create_database_connection()
    page_number = request.args.get('page') if request.args.get('page') is not None else 0
    start_range = int(page_number) * 9
    end_range = start_range + 9
    data = server.get_query_result(f"SELECT * FROM songs WHERE channel_id = '{channel_id}' ORDER BY upload_date DESC LIMIT {str(start_range)}, {str(end_range)}")
    videos = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    if len(videos) == 0:
        return render_template("search_no_result.html", search_terms="No videos found")
    channel_name = videos[0]["channel_name"]
    server.close_connection()
    return render_template("channel.html",
                           videos=videos,
                           thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
                           channel_name=channel_name,)

@app.route("/status")
def status_page():
    database_status = "Online"
    try:
        server = create_database_connection()
        server.close_connection()
    except:
        database_status = "Offline"
        render_template("status.html",
                        database_status=database_status,
                        )
    server = create_database_connection()
    worker_data = server.get_query_result("SELECT * FROM worker_status")
    workers = []
    for worker in worker_data:
        worker_dict = {}
        worker_dict["name"] = worker[1]
        worker_dict["status"] = worker[3]
        worker_dict["timestamp"] = worker[4]
        workers.append(worker_dict)
    
    return render_template("status.html",
                           database_status=database_status,
                           workers = workers,
                           )

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
def api_get_random_video():
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


@app.route("/api/stats")
def api_get_stats():
    server = create_database_connection()
    song_count = server.get_query_result("SELECT COUNT(video_id) FROM songs")
    return jsonify({"song_count": song_count[0][0]})

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

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

    if server.check_row_exists("archive_queue", "url", url):
        server.close_connection()
        return "Already queued"
    server.insert_row("archive_queue", "url", (url,))
    server.insert_row("archive_log", "url, user, status, timestamp", (url, password, "Queued", datetime.datetime.now()))
    server.close_connection()
    return "OK", 200


def get_next_video_in_queue():
    """
    Gets the next video in the queue
    """
    server = create_database_connection()
    try:
        next_video = server.get_query_result("SELECT url FROM archive_queue ORDER BY id LIMIT 1;")[0][0]
    except IndexError:
        server.close_connection()
        return None
    server.delete_row("archive_queue", "url", (next_video,))
    server.close_connection()
    return next_video


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
    next_video = get_next_video_in_queue()
    if next_video is None:
        server.close_connection()
        return "No videos in queue", 204
    server.update_row("archive_log", "url", next_video, "status", "Processed",)
    server.close_connection()
    return next_video

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


if __name__ == "__main__":
    app.run(debug=True)
