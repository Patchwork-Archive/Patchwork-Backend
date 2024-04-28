create table archive_log
(
    id        int auto_increment
        primary key,
    url       text         not null,
    user      varchar(128) not null,
    status    text         not null,
    timestamp text         null
);

create table archive_queue
(
    id   int auto_increment
        primary key,
    url  text null,
    mode int  null
);

create table archive_queue_auth
(
    id    int auto_increment
        primary key,
    token varchar(128) null
);

create table archive_worker_auth
(
    id    int auto_increment
        primary key,
    token varchar(128) not null
);

create index archive_worker_auth_token
    on archive_worker_auth (token);

create table kv
(
    DATA      varchar(255) not null
        primary key,
    REFERENCE varchar(255) null
);

create table songs
(
    video_id     varchar(255) not null,
    title        text         not null,
    channel_name text         not null,
    channel_id   varchar(255) not null,
    upload_date  text         not null,
    description  text         not null,
    id           int auto_increment
        primary key
);

create table channels
(
    channel_id     varchar(255) not null
        primary key,
    channel_name   text         not null,
    romanized_name text         null,
    description    text         null,
    constraint channel_id_exists
        foreign key (channel_id) references songs (channel_id)
);

create table romanized
(
    id              int auto_increment
        primary key,
    video_id        varchar(255) not null,
    romanized_title text         not null,
    constraint video_id_exists
        foreign key (video_id) references songs (video_id)
            on delete cascade
);

create index idx_songs_on_channel_id
    on songs (channel_id);

create index idx_songs_on_video_id
    on songs (video_id);

create table worker_status
(
    id        int          not null
        primary key,
    name      text         null,
    token     varchar(128) null,
    status    text         null,
    timestamp text         null,
    constraint valid_worker
        foreign key (token) references archive_worker_auth (token)
);
