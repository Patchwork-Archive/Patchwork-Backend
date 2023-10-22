# Patchwork Backend
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white)

A Python Flask server that serves archived videos and metadata from a MySQL database. A bunch of stuff patched together.
- A Flask based server that serves archived videos and thumbnails from storage
- Metadata is stored and served from a MySQL database
- Able to track a queue of videos to be archived
- Able to track workers which automatically download and upload videos to storage


## Deploying
```bash
git clone https://github.com/pinapelz/Patchwork-Flask.git && cd Patchwork-Flask
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
```
Configure `config.ini` according to your needs. Leave `ssh` and `remote_bind` blank if you are not using a remote MySQL server.

## Storage Statistics
`accountId` and `api_token` are optional fields for connecting to an external API to retrieve storage statistics. By default, `manual_storage_data.py` is used and pulls data from the kv tables of your MySQL DB.

- For other storage providers, create a new class in a new Python module within the `webapi` directory which inherits from abstract class `storage_api`. Implement the `get_storage_used` and `get_number_of_files` methods

- Modify the `[storage]` section in  `config.ini` with any additional authentication fields required by your storage provider

- Then modify `flask_app.py` to use your new class. Authentication fields can be accessed via `CONFIG['storage']['FIELD_NAME']`

**Alternatively leave this field empty to not return storage statistics**

## Using the queue
To add videos to the queue for workers to process send a POST request to the `/api/worker/queue` endpoint
```bash
curl -X POST -H "X-AUTHENTICATION: YOUR_QUEUE_TOKEN" -d "url=VIDEO_URL" http://localhost:5000/api/worker/queue
```

To read from the queue send a GET request to the `/api/worker/next` endpoint
```bash
curl -X GET -H "X-AUTHENTICATION: YOUR_WORKER_TOKEN" http://localhost:5000/api/worker/next
```

## DBM (Database Manager)
Run `dbm.py` to create the necesarry tables in your database
```bash
python dbm.py
```
### Adding Worker Tokens
Tokens are not automatically generated. 

To create new tokens for workers, run `dbm.py` with the `--addworkertoken` flag
- All workers you deploy will need a token to be able to read from the queue and write its results to the database

To create new tokens for queuers, run `dbm.py` with the `--addqueuetoken` flag
- Anyone who has a token can add videos to the `archive_queue` table which workers will then read from.

```bash
python dbm.py --addqueuetoken "THE_QUEUE_TOKEN_YOU_WANT_TO_USE" --addworkertoken "THE_WORKER_TOKEN_YOU_WANT_TO_USE"
```

Run `flask_app.py` with the WSIG server of your choice or directly.
