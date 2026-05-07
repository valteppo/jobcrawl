-- schema

CREATE TABLE IF NOT EXISTS ala (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    base_url TEXT NOT NULL
);

INSERT OR IGNORE INTO ala (name, base_url) 
VALUES ('ohjelmisto_ala', 'https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys');

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER UNIQUE,
    ala_id INTEGER,
    url TEXT,
    company TEXT,
    publish_date TIMESTAMP,
    expiry_date TIMESTAMP,
    language TEXT,
    evaluated INTEGER DEFAULT 0,
    ranking INTEGER DEFAULT -1,
    description TEXT,
    application TEXT,
    contact TEXT,
    FOREIGN KEY (ala_id) REFERENCES ala(id));
