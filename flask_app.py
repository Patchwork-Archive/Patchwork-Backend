from flask import Flask, render_template, request, jsonify
import fileutil
from sql_handler import SQLHandler
from flask_cors import CORS

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


@app.route("/")
def random_video_player():
    return render_template(
        "random_video.html",
        domain=SITE_CONFIG["domain"],
        cdn=SITE_CONFIG["cdn"],
        humbnails_domain=SITE_CONFIG["thumbnails_domain"],
        )

@app.route("/watch")
def watch_video():
    server = create_database_connection()
    video_id = request.args.get('v')
    print(video_id)
    if server.check_row_exists(table_name="songs", column_name="video_id", value=video_id):
        data = server.get_query_result(f"SELECT * FROM songs WHERE video_id = '{video_id}'")
        return render_template(
            "specific_video.html",
            video_id=data[0][0],
            domain=SITE_CONFIG["domain"],
            cdn=SITE_CONFIG["cdn"],
            humbnails_domain=SITE_CONFIG["thumbnails_domain"],
        )
    server.c
    server.close_connection()
    return render_template("404.html")

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

if __name__ == "__main__":
    app.run(debug=True)
