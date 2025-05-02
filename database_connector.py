import mysql.connector


def create_connection(database='mpesa_sim'):
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='1998',
        database=database,
    )


# Test the connection
def test_mysql_connection():
    try:
        connection = create_connection()
        if connection.is_connected():
            print("\033[92mConnection successful!\033[0m")
            print("Connected to MySQL Server version:", connection.get_server_info())

        else: print("\033[91mConnection failed!\033[0m")

    except Error as e: print(f"\033[91mError: {e}\033[0m")

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("MySQL connection is closed.")


if __name__ == '__main__':
    test_mysql_connection()