CREATE SCHEMA IF NOT EXISTS patchwork_archive;

-- =====================
-- Sequences
-- =====================

CREATE SEQUENCE patchwork_archive.archive_log_id_seq;
CREATE SEQUENCE patchwork_archive.archive_queue_id_seq;
CREATE SEQUENCE patchwork_archive.archive_queue_auth_id_seq;
CREATE SEQUENCE patchwork_archive.archive_worker_auth_id_seq;
CREATE SEQUENCE patchwork_archive.romanized_id_seq;
CREATE SEQUENCE patchwork_archive.songs_id_seq;

-- =====================
-- Tables
-- =====================

CREATE TABLE patchwork_archive.archive_log (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.archive_log_id_seq'),
    url text NOT NULL,
    "user" varchar(128) NOT NULL,
    status text NOT NULL,
    "timestamp" text
);

CREATE TABLE patchwork_archive.archive_queue (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.archive_queue_id_seq'),
    url text,
    mode integer
);
CREATE TABLE patchwork_archive.archive_queue_auth (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.archive_queue_auth_id_seq'),
    token varchar(128)
);

CREATE TABLE patchwork_archive.archive_worker_auth (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.archive_worker_auth_id_seq'),
    token varchar(128) NOT NULL
);

CREATE TABLE patchwork_archive.channels (
    channel_id varchar(255) PRIMARY KEY,
    channel_name text NOT NULL,
    romanized_name text,
    description text
);

CREATE TABLE patchwork_archive.files (
    video_id varchar(255) PRIMARY KEY,
    size_mb double precision,
    extension varchar(32)
);

CREATE TABLE patchwork_archive.kv (
    data varchar(255) PRIMARY KEY,
    reference varchar(255)
);

CREATE TABLE patchwork_archive.romanized (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.romanized_id_seq'),
    video_id varchar(255) NOT NULL,
    romanized_title text NOT NULL
);

CREATE TABLE patchwork_archive.songs (
    id integer PRIMARY KEY DEFAULT nextval('patchwork_archive.songs_id_seq'),
    video_id varchar(255) NOT NULL,
    title text NOT NULL,
    channel_name text NOT NULL,
    channel_id varchar(255) NOT NULL,
    upload_date text NOT NULL,
    description text NOT NULL
);

CREATE TABLE patchwork_archive.views (
    video_id varchar(255) PRIMARY KEY,
    view_count integer NOT NULL
);

CREATE TABLE patchwork_archive.worker_status (
    id integer PRIMARY KEY,
    name text,
    token varchar(128),
    status text,
    "timestamp" text
);

-- =====================
-- Indexes
-- =====================

CREATE INDEX idx_archive_worker_auth_token
    ON patchwork_archive.archive_worker_auth (token);

CREATE INDEX idx_romanized_video_id
    ON patchwork_archive.romanized (video_id);

CREATE INDEX idx_songs_channel_id
    ON patchwork_archive.songs (channel_id);

CREATE INDEX idx_songs_video_id
    ON patchwork_archive.songs (video_id);

CREATE INDEX idx_worker_status_token
    ON patchwork_archive.worker_status (token);
