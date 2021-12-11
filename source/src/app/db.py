import sqlite3
from sqlite3 import Error
import numpy as np

########################################################################

database_path = ""

########################################################################


def create_connection():
    """create a databaseconnection to the SQLite database
    :return: Connection object or None
    """
    conn = None
    global database_path
    database_path = "/data/database.db"

    try:
        conn = sqlite3.connect(database_path)
    except Error as e:
        print(e)

    return conn


########################################################################


def create_table_if_missing():

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
    course_id integer,
    username text,
    action_date date,
    file_name text,
    file_path text,
    PRIMARY KEY (course_id, username, action_date, file_name)
    );
    """

    conn = create_connection()

    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")

    return conn


########################################################################


def add_file(conn, file):
    """
    Create a new project into the files table
    :param conn:
    :param file:
    """
    sql = """
    INSERT INTO files (course_id, username, action_date, file_name, file_path)
    VALUES(?,?,?,?,?);
    """
    cur = conn.cursor()
    cur.execute(sql, file)
    conn.commit()


########################################################################


def get_files_first_version(conn, course_id):
    """
    Get all files with the given course_id
    :param conn:
    :param course_id:
    """
    # sql = """
    # SELECT *
    # FROM files
    # WHERE course_id = ?
    # """

    sql = """
    SELECT course_id, username, action_date, file_name, file_path
    FROM files where (file_name, action_date) in (
        SELECT file_name, min(action_date) as action_date
        FROM files
        WHERE course_id = ?
        GROUP BY file_name
    );
    """

    cur = conn.cursor()
    cur.execute(sql, course_id)

    alist = cur.fetchall()
    files = np.array(alist)

    return files


########################################################################
########################## PUBLIC FUNCTIONS ############################
########################################################################

########################################################################


def add_file_public(course_id, user_username, date, file_name, file_path):
    conn = create_table_if_missing()
    if conn is not None:
        try:
            file = (course_id, user_username, date, file_name, file_path)
            add_file(conn, file)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")


########################################################################


def get_files_first_version_public(course_id):
    conn = create_table_if_missing()

    files = []
    if conn is not None:
        try:
            files = get_files_first_version(conn, course_id)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")

    return files


########################################################################
