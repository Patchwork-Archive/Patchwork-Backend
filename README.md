# Video-Archive-Server

A Python Flask server that serves archived videos and metadata from a MySQL database. A bunch of stuff patched together.

## Key Points
- A Flask based server that serves archived videos and thumbnails from storage
- Metadata is stored and served from a MySQL database
- Able to track a queue of videos to be archived
- Able to track workers which automatically download and upload videos to storage


## Getting Started
```bash
git clone https://github.com/pinapelz/Video-Archive-Server.git && cd Video-Archive-Server
<<<<<<< HEAD
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate.bat on Windows
=======
>>>>>>> master
pip install -r requirements.txt
```
Configure `config.ini` according to your needs. Leave `ssh` and `remote_bind` blank if you are not using a remote MySQL server.

`accountId` and `api_token` are authetication fields for the storage usage statistics on the dashboard. The code in the repo is configured to use Cloudflare R2 storage and as such calls the Cloudflare API to get the storage usage statistics

- For other storage providers, create a new class in a new Python module within the `webapi` directory which inherits from abstract class `storage_api`. Implement the `get_storage_used` and `get_number_of_files` methods

- Modify the `[storage]` section in  `config.ini` with any additional authentication fields required by your storage provider

- Then modify `flask_app.py` to use your new class rather than `CloudflareAPI`. Authentication fields can be accessed via `CONFIG['storage']['FIELD_NAME']`

**Alternatively leaving this field empty and not show storage statistics**

<<<<<<< HEAD
### Deploy
To deploy the server, run `flask_app.py` with the WSIG server of your choice or directly.
=======
>>>>>>> master

---

![image](https://github.com/pinapelz/Video-Archive-Server/assets/21994085/eb626166-f6db-43c9-89d3-4986c6a8d2cd)

![image](https://github.com/pinapelz/Video-Archive-Server/assets/21994085/2602aadb-5b33-4659-9da5-117aa2f92e3f)

![image](https://github.com/pinapelz/Video-Archive-Server/assets/21994085/16646e1e-977c-4c92-92e8-4d18963a2db4)

An optional and very messy archiving script can be found [here](https://github.com/pinapelz/Video-Archive-Worker)

The overall design and idea is heavily inspired by [Ragtag Archive](https://archive.ragtag.moe/)