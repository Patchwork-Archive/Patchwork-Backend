from flask import Flask, render_template, request, jsonify
import fileutil
from sql_handler import SQLHandler
from flask_cors import CORS
from webapi.cloudflare import CloudflareAPI
import random
import datetime
import re

app = Flask(__name__)
CORS(app)


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

@app.route("/random")
def random_video_player():
    return render_template(
        "random_video.html",
        domain=SITE_CONFIG["domain"],
        cdn=SITE_CONFIG["cdn"],
        thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
        )

@app.route("/")
def landing_page():
    server = create_database_connection()
    storage_api = CloudflareAPI(CONFIG["storage"]["api_token"], CONFIG["storage"]["accountID"], CONFIG["storage"]["bucket_name"])
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
    server.close_connection()
    number_of_files = int(storage_api.get_number_of_files())
    return render_template("landing.html", 
                            videos=videos,
                            domain=SITE_CONFIG["domain"],
                            thumbnails_domain=SITE_CONFIG["thumbnails_domain"],
                            recent_archived_videos=recent_archived_videos,
                            featured_videos=featured_videos,
                            archived_videos_count=f"{number_of_files:,}" if number_of_files >= 10000 else str(number_of_files), #　Pretty print the number of files
                            archive_size=str(round(int(storage_api.get_storage_used())/ (1024 **3), 2)),
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
                                video_title = video_data[0][1],
                                channel_name = video_data[0][2],
                                upload_date = video_data[0][4],
                                description = description,
                               )
    server.close_connection()
    return render_template("404.html")

@app.route("/results")
def search_query():
    server = create_database_connection()
    search_terms = request.args.get('search_query')
    data = server.search_video_row("songs", search_terms.split(), 14)
    server.close_connection()
    search_result = [{"video_id": video[0], "title": video[1], "channel_name": video[2], "channel_id": video[3], "upload_date": video[4], "description": video[5]} for video in data]
    return render_template("search.html", 
                           search_result=search_result,
                           search_terms = search_terms,
                           thumbnails_domain=SITE_CONFIG["thumbnails_domain"],)

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


@app.route("/api/stats")
def api_get_stats():
    server = create_database_connection()
    song_count = server.get_query_result("SELECT COUNT(video_id) FROM songs")
    return jsonify({"song_count": song_count[0][0]})

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True, port=8000)
