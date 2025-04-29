import mysql.connector


class Sql_commands:
    def __init__(self) -> None:
        self.conn = self.create()
        self.cursor = self.conn.cursor()

    def create(self) -> None:
        connection = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '1998'
        )

        return connection

    ''' The function create the sql database based on the created schema'''
    def run_sql_file(self, file_path):
        with open(file_path, 'r') as f:
            sql = f.read()
            for statement in sql.split(';'):
                if statement.strip():
                    self.cursor.execute(statement)

        self.conn.commit()

    def delete_sql_database(self):
        self.cursor.execute("DROP DATABASE IF EXISTS mpesa_sim;")
        self.conn.commit()
        print("Database deleted.")

    def __del__(self):
        """ Close the sql connection """
        if hasattr(self, 'cursor'): self.cursor.close()
        if hasattr(self, 'conn'): self.conn.close()


def main_sql():
    print('1. Run SQL file')
    print('2. Delete SQL database')
    question: int = int(input('Which option do you choose?: '))
    callback = Sql_commands()

    if question == 1:
        callback.run_sql_file('create_tables.sql')
        print('Database has been created Successfully')

    elif question == 2:
        callback.delete_sql_database()
        print('Database has been deleted successfully')

    else: raise ValueError ('Please input the correct value')


if __name__ == '__main__':
    main_sql()