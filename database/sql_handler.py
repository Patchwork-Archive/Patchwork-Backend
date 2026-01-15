import psycopg2
from psycopg2 import Error, sql
import os
import dotenv

dotenv.load_dotenv()

class SQLHandler:
    def __init__(self):
        self.connection = self._create_server_connection()
        self.schema = "patchwork_archive"

    def _create_server_connection(self) -> psycopg2.extensions.connection:
        connection = None
        try:
            connection = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                database=os.environ.get("DB_DATABASE"),
                user=os.environ.get("DB_USERNAME"),
                password=os.environ.get("DB_PASSWORD"),
                port=os.environ.get("DB_PORT", "5432")
            )
            connection.autocommit = False
        except Error as err:
            print(f"Error: '{err}'")
        if connection is None:
            print("Connection failed")
            exit(1)
        return connection

    def get_connection(self):
        return self.connection

    def _create_database(self, cursor, database_name: str):
        try:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(database_name)))
        except Error as err:
            print(f"Failed creating database: {err}")
            exit(1)

    def _load_database(self, database_name: str):
        try:
            cursor = self.connection.cursor()
            cursor.close()
            print(f"Database {database_name} loaded successfully")
        except Error as err:
            print(f"Failed to load database: {err}")
            exit(1)

    def create_table(self, name: str, column: str):
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{name}"
            cursor.execute(f"CREATE TABLE {full_table_name} ({column})")
            self.connection.commit()
            print(f"Table {name} created successfully")
        except Error as err:
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def insert_row(self, table_name: str, column: str, data: tuple):
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{table_name}"
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {full_table_name} ({column}) VALUES ({placeholders})"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Inserted:", data)
        except Error as err:
            print("Error inserting data")
            print(err)
            self.connection.rollback()
            if "duplicate key" in str(err).lower():
                return True
            return False
        finally:
            cursor.close()
        return True

    def close_connection(self):
        if self.connection and not self.connection.closed:
            if hasattr(self, '_tunnel'):
                self._tunnel.stop()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def clear_table(self, name: str):
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{name}"
            cursor.execute(f"DELETE FROM {full_table_name}")
            self.connection.commit()
            print("Table cleared successfully")
        except Error as err:
            print("Error clearing table")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def reset_auto_increment(self, name: str):
        cursor = self.connection.cursor()
        try:
            # PostgreSQL uses sequences instead of auto_increment
            sequence_name = f"{self.schema}.{name}_id_seq"
            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")
            self.connection.commit()
            print("Sequence reset successfully")
        except Error as err:
            print("Error resetting sequence")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def copy_rows_to_new_table(self, name: str, new_name: str, column: str):
        cursor = self.connection.cursor()
        try:
            full_old_table = f"{self.schema}.{name}"
            full_new_table = f"{self.schema}.{new_name}"
            cursor.execute(
                f"INSERT INTO {full_new_table} ({column}) SELECT {column} FROM {full_old_table}")
            self.connection.commit()
            print("Rows copied successfully")
        except Error as err:
            print("Error copying rows")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def drop_table(self, name: str):
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{name}"
            cursor.execute(f"DROP TABLE {full_table_name}")
            self.connection.commit()
            print("Table dropped successfully")
        except Error as err:
            print("Error dropping table")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def check_row_exists(self, table_name: str, column_name: str, value: str) -> bool:
        """
        Checks if a row exists in a table
        """
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{table_name}"
            query = f"SELECT * FROM {full_table_name} WHERE {column_name} = %s"
            cursor.execute(query, (value,))
            result = cursor.fetchone()
            return result is not None
        except Error as err:
            print("Error checking row")
            print(err)
            return False
        finally:
            cursor.close()

    def update_row(self, name: str, column_name: str, search_val: str, replace_col: str, new_value: str):
        """
        Updates a row in a table
        """
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{name}"
            query = f"UPDATE {full_table_name} SET {replace_col} = %s WHERE {column_name} = %s"
            cursor.execute(query, (new_value, search_val))
            self.connection.commit()
            print("Row updated successfully")
        except Error as err:
            print("Error updating row")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple = ()):
        """
        Executes a given query without fetching results and indicates if it was successful.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            print("Query executed successfully")
            return True
        except Error as err:
            print("Error executing query")
            print(err)
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def get_query_result(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error executing query")
            print(err)
            return None
        finally:
            cursor.close()

    def delete_row(self, name: str, column: str, data: tuple):
        cursor = self.connection.cursor()
        try:
            full_table_name = f"{self.schema}.{name}"
            query = f"DELETE FROM {full_table_name} WHERE {column} = %s"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Deleted:", data)
        except Error as err:
            print("Error deleting data")
            print(err)
            self.connection.rollback()
            return False
        finally:
            cursor.close()
        return True

    def get_random_row(self, table_name: str, limit: int = 1):
        """
        Retrieves a random row from a table
        """
        cursor = self.connection.cursor()
        try:
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("Limit must be a positive integer")
            full_table_name = f"{self.schema}.{table_name}"
            query = f"SELECT * FROM {full_table_name} ORDER BY RANDOM() LIMIT %s"
            cursor.execute(query, (limit,))
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error getting random row")
            print(err)
        except ValueError as ve:
            print("Validation error:", ve)
        finally:
            cursor.close()

    def search_row(self, table_name: str, col_name: str, keywords: list, limit: int = 1, offset: int = 0):
        """
        Searches for rows in the specified table with the given keywords.
        """
        cursor = self.connection.cursor()
        if not table_name.replace('_', '').isalnum() or not col_name.replace('_', '').isalnum():
            raise ValueError("Invalid table or column name")

        full_table_name = f"{self.schema}.{table_name}"
        query = f"SELECT * FROM {full_table_name} WHERE 1=1"
        keyword_conditions = []
        for keyword in keywords:
            keyword_condition = f"LOWER({col_name}) LIKE %s"
            formatted_keyword = f"%{keyword.lower()}%"
            keyword_conditions.append((keyword_condition, formatted_keyword))
        if keyword_conditions:
            query += " AND " + " AND ".join([condition[0] for condition in keyword_conditions])
        count_query = query
        query += " LIMIT %s OFFSET %s"
        try:
            cursor.execute(count_query, [condition[1] for condition in keyword_conditions])
            result_count = len(cursor.fetchall())

            cursor.execute(query, [condition[1] for condition in keyword_conditions] + [limit, offset])
            result = cursor.fetchall()

            return result, result_count
        except Error as err:
            print("Error searching row")
            print(err)
        finally:
            cursor.close()

    def search_romanized_video(self, table_name: str, target_col: str, keywords: list, limit: int = 1, offset: int = 0):
        """
        Searches for videos in the specified table with romanized keywords.
        """
        cursor = self.connection.cursor()
        if not table_name.replace('_', '').isalnum() or not target_col.replace('_', '').isalnum():
            raise ValueError("Invalid table or column name")
        full_table_name = f"{self.schema}.{table_name}"
        romanized_table = f"{self.schema}.romanized"
        query = f"SELECT * FROM {full_table_name} S JOIN {romanized_table} R on S.video_id=R.video_id WHERE 1=1"
        keyword_conditions = []
        for keyword in keywords:
            # PostgreSQL uses ~* for case-insensitive regex
            keyword_condition = f"LOWER({target_col}) ~ %s"
            # PostgreSQL word boundary in regex: \y or use [[:<:]] and [[:>:]]
            formatted_keyword = f"\\m{keyword.lower()}\\M"
            keyword_conditions.append((keyword_condition, formatted_keyword))
        if keyword_conditions:
            query += " AND " + " AND ".join([condition[0] for condition in keyword_conditions])
        count_query = query
        query += " LIMIT %s OFFSET %s"
        try:
            cursor.execute(count_query, [condition[1] for condition in keyword_conditions])
            result_count = len(cursor.fetchall())

            cursor.execute(query, [condition[1] for condition in keyword_conditions] + [limit, offset])
            result = cursor.fetchall()
            return result, result_count
        except Error as err:
            print("Error searching video row")
            print(err)
        finally:
            cursor.close()

    def search_romanized_channel(self, table_name: str, keywords: list, limit: int = 1, offset: int = 0):
        """
        Searches for channels in the specified table with romanized keywords.
        """
        cursor = self.connection.cursor()
        if not table_name.replace('_', '').isalnum():
            raise ValueError("Invalid table name")

        full_table_name = f"{self.schema}.{table_name}"
        query = f"SELECT * FROM {full_table_name} WHERE 1=1"
        keyword_conditions = []

        for keyword in keywords:
            keyword_condition = f"LOWER(romanized_name) ~ %s"
            formatted_keyword = f"\\m{keyword.lower()}\\M"
            keyword_conditions.append((keyword_condition, formatted_keyword))
        if keyword_conditions:
            query += " AND " + " AND ".join([condition[0] for condition in keyword_conditions])
        count_query = query
        query += " LIMIT %s OFFSET %s"
        try:
            cursor.execute(count_query, [condition[1] for condition in keyword_conditions])
            result_count = len(cursor.fetchall())
            cursor.execute(query, [condition[1] for condition in keyword_conditions] + [limit, offset])
            result = cursor.fetchall()
            return result, result_count
        except Error as err:
            print("Error searching channel row")
            print(err)
        finally:
            cursor.close()

    def search_channel_row(self, table_name: str, keywords: list, limit: int = 1, offset: int = 0):
        cursor = self.connection.cursor()
        full_table_name = f"{self.schema}.{table_name}"
        query = f"SELECT * FROM {full_table_name} WHERE 1=1"
        keyword_conditions = []
        for keyword in keywords:
            keyword_condition = f"LOWER(channel_name) LIKE %s"
            formatted_keyword = f"%{keyword.lower()}%"
            keyword_conditions.append((keyword_condition, formatted_keyword))
        if keyword_conditions:
            query += " AND " + " AND ".join([condition[0] for condition in keyword_conditions])
        count_query = query
        query += " LIMIT %s OFFSET %s"

        try:
            cursor.execute(count_query, ([condition[1] for condition in keyword_conditions]))
            result_count = len(cursor.fetchall())
            cursor.execute(query, [condition[1] for condition in keyword_conditions] + [limit, offset])
            result = cursor.fetchall()
            return result, result_count
        except Error as err:
            print("Error searching channel row")
            print(err)
        finally:
            cursor.close()
