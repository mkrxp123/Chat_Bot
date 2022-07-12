CREATE TABLE
    if NOT EXISTS Users(
        UID INTEGER PRIMARY KEY NOT NULL,
        U_name VARCHAR(256) NOT NULL
    );
CREATE TABLE
    if NOT EXISTS Memo(
        MID INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time datetime DEFAULT (datetime('now', 'localtime')) NOT NULL,
        duration INTEGER NOT NULL,
        content NVARCHAR(256) NOT NULL,
        UID INTEGER NOT NULL,
        FOREIGN key (UID) REFERENCES Users(UID)
    );