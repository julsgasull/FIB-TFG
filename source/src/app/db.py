import sqlite3
from sqlite3 import Error

########################################################################


def create_table(db_file):

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
    course_id integer,
    username text,
    action_date date,
    file_path text,
    PRIMARY KEY (course_id, username, action_date, file_path)
    );
    """

    conn = create_connection(db_file)

    if conn is not None:
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)
    else:
        print("Error! cannot create the database connection.")


########################################################################


def create_connection(db_file):
    """create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


########################################################################


def create_file(conn, file):
    """
    Create a new project into the files table
    :param conn:
    :param file:
    :return: project id
    """
    sql = """ INSERT INTO files ( course_id, username, action_date, file_path )
              VALUES(?,?,?,?) """
    cur = conn.cursor()
    cur.execute(sql, file)
    conn.commit()
    return cur.lastrowid


########################################################################


def main():
    database = "../data/database.db"

    # create a database connection
    conn = create_connection(database)
    with conn:
        # create a new file
        file = (1, "juls", "2021-09-18", "../media/test2.txt")
        file_id = create_file(conn, file)


########################################################################

if __name__ == "__main__":
    main()

########################################################################
