import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_db_connection():
    try:
        # Fetch environment variables for MySQL connection
        host = os.getenv("DB_HOST", "localhost")  # Default to localhost if not set
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        port = os.getenv("DB_PORT", 3306)  # Default to 3306 if port is not set

        # Check if necessary environment variables are present
        if not all([host, database, user, password]):
            raise ValueError("Missing database connection environment variables")

        # Create the MySQL connection with optional port
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port  # Specify port if needed
        )

        # Check if the connection is successful
        if connection.is_connected():
            print(f"Connected to MySQL database: {database}")
            return connection
        else:
            raise ConnectionError("Failed to connect to the database")

    except ValueError as e:
        print(f"ValueError: {e}")
        return None
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
