import sqlite3
from sqlite3 import Error

########################################################################

DATABASE_PATH = "../../data/db/database.db"

########################################################################


def create_connection():
    """create a database connection to the SQLite database
    specified by db_file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except Error as e:
        print(e)

    return conn


########################################################################


def create_table():
    conn = create_connection()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
    course_id integer,
    username text,
    action_date date,
    file_name text,
    PRIMARY KEY (course_id, username, action_date, file_path)
    );
    """

    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")


########################################################################


def upload_file(file_info):
    """Create a new file into the files table
    :param file_info: format = (course_id, username, action_date, file_path)
    """
    conn = create_connection()

    insert_line_sql = """ 
    INSERT INTO files(course_id, username, action_date, file_path)
    VALUES(?,?,?,?) 
    """

    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(insert_line_sql)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")


########################################################################
