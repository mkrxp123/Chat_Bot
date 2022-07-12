CREATE TABLE
    if NOT EXISTS Count(
        name NVARCHAR(32) PRIMARY KEY NOT NULL,
        count INTEGER DEFAULT 1 NOT NULL
    );
CREATE TABLE
    if NOT EXISTS Images(
        I_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name NVARCHAR(32) NOT NULL,
        image BLOB UNIQUE NOT NULL,
        image_type VARCHAR(8) NOT NULL,
        FOREIGN key (name) REFERENCES Count(name)
    );