"""
Database connection management
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_database_connection():
    """
    Create and return MySQL database connection
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'srv719.hstgr.io'),
            database=os.getenv('DB_NAME', 'u272626296_automacoes'),
            user=os.getenv('DB_USER', 'u272626296_mesapremium'),
            password=os.getenv('DB_PASSWORD'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=True,
            pool_name='api_pool',
            pool_size=10,
            pool_reset_session=True
        )
        
        if connection.is_connected():
            logger.info("Successfully connected to MySQL database")
            return connection
            
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        return None

def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Execute database query with error handling
    """
    connection = None
    cursor = None
    result = None
    
    try:
        connection = get_database_connection()
        if not connection:
            raise Exception("Failed to connect to database")
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.rowcount
            
    except Error as e:
        logger.error(f"Database query error: {e}")
        if connection:
            connection.rollback()
        raise e
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            
    return result