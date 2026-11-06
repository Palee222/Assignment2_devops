import os 
#Imports Python’s built-in operating system module, used to read environment variables and manage file paths.
import sqlite3
#Imports the SQLite database library, which lets Python connect to and work with SQLite databases.
from pathlib import Path
#makes it easier to work with file and folder paths

DATA_DIR = os.getenv("DATA_DIR", "data")
#Reads the environment variable DATA_DIR. If it is not set, it defaults to the folder name "data".
DB_PATH = Path(DATA_DIR) / "secnote.db"
#Builds the full path to the database file: a folder named data (or whatever DATA_DIR is)

def get_connection():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True) #Creates the data directory if it does not already exis
    conn = sqlite3.connect(DB_PATH)
    #Opens a connection to the SQLite database at DB_PATH.
    conn.row_factory = sqlite3.Row
    #Tells SQLite to return rows as dictionary-like objects instead of plain tuples. This makes data access easier.
    return conn #Returns the open database connection so other functions can use it.

def insert(table, values):
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    conn = get_connection()
    try:
        cur = conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        conn.commit()
        if cur.lastrowid is None:
            raise RuntimeError(f"The {table} record was not inserted.")
        return cur.lastrowid
    except sqlite3.Error as error:
        conn.rollback()
        raise RuntimeError(f"Could not insert into {table}: {error}") from error
    finally:
        conn.close()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    #tables get created if they do not already exist
    # incidents
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    # tags
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)
    # incident_tags
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incident_tags (
            incident_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        );
    """)
    # weak_passwords
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL,
            source TEXT
        );
    """)
    # password_rules
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            min_length INTEGER,
            require_upper INTEGER,
            require_lower INTEGER,
            require_digit INTEGER,
            require_symbol INTEGER
        );
    """)
    conn.commit() #Saves all the SQL changes made so far to the database.
    conn.close() #Closes the connection properly when the setup is finished.