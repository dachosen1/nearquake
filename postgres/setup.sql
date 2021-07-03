create table coordinate
(
    ids       text,
    longitude numeric(1000),
    latitude  numeric(1000),
    depth     numeric(1000)
);


create table last_update
(
    last_date date,
    last_time time,
    id        serial not null
);


-- auto-generated definition
create table properties
(
    mag         numeric(1000),
    place       text,
    time        timestamp,
    updated     timestamp,
    tz          integer,
    felt        integer,
    cdi         numeric(1000),
    mmi         double precision,
    alert       text,
    status      text,
    tsunami     integer,
    sig         integer,
    net         text,
    code        text,
    ids         text,
    source      text,
    types       text,
    nst         integer,
    dmin        integer,
    rms         integer,
    gap         integer,
    "magType"   text,
    quake_title text,
    quake_type  text
);




