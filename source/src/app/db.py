import sqlite3
from sqlite3 import Error

########################################################################

database_path = ""

########################################################################


def create_table_if_missing():

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
    course_id integer,
    username text,
    action_date date,
    file_path text,
    PRIMARY KEY (course_id, username, action_date, file_path)
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


def create_file(conn, file):
    """
    Create a new project into the files table
    :param conn:
    :param file:
    """
    sql = """
    INSERT INTO files (course_id, username, action_date, file_path)
    VALUES(?,?,?,?);
    """
    cur = conn.cursor()
    cur.execute(sql, file)
    conn.commit()


########################################################################


def addRow(course_id, user_username, date, file_path):
    conn = create_connection()
    with conn:
        # create a new file
        file = (course_id, user_username, date, file_path)
        create_file(conn, file)


########################################################################


# def main():
#     # create a database connection
#     conn = create_connection(database_path)
#     with conn:
#         # create a new file
#         file = (1, "juls", "2021-09-18", "../media/test2.txt")
#         file_id = create_file(conn, file)


# ########################################################################

# if __name__ == "__main__":
#     main()

# ########################################################################
