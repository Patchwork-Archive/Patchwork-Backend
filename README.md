# Video-Archive-Server

A Python Flask server that serves archived videos and metadata from a MySQL database.

Videos and thumbnails can be hosted in a S3 compatible bucket and served through a CDN.

A very messy archiving script can be found [here](https://github.com/pinapelz/Video-Archive-Worker) however so long as the database is populated with the correct information, the server will work.

Search is not implemented yet

---
![image](https://github.com/pinapelz/Video-Archive-Server/assets/21994085/eb626166-f6db-43c9-89d3-4986c6a8d2cd)

![image](https://github.com/pinapelz/Video-Archive-Server/assets/21994085/2602aadb-5b33-4659-9da5-117aa2f92e3f)

The overall design and idea is heavily inspired by [Ragtag Archive](https://archive.ragtag.moe/)