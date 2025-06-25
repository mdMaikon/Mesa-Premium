"""
Database connection management with connection pooling
"""
import mysql.connector
from mysql.connector import Error, pooling
import os
from dotenv import load_dotenv
import logging
from contextlib import contextmanager
from utils.log_sanitizer import get_sanitized_logger

# Load environment variables
load_dotenv()

logger = get_sanitized_logger(__name__)

# Global connection pool instance
_connection_pool = None

def get_connection_pool():
    """
    Create and return MySQL connection pool (singleton pattern)
    """
    global _connection_pool
    
    if _connection_pool is None:
        try:
            pool_config = {
                'pool_name': 'api_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'host': os.getenv('DB_HOST', 'srv719.hstgr.io'),
                'database': os.getenv('DB_NAME', 'u272626296_automacoes'),
                'user': os.getenv('DB_USER', 'u272626296_mesapremium'),
                'password': os.getenv('DB_PASSWORD'),
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': True
            }
            
            _connection_pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info("MySQL connection pool created successfully")
            
        except Error as e:
            logger.error(f"Error creating MySQL connection pool: {e}")
            raise e
    
    return _connection_pool

@contextmanager
def get_database_connection():
    """
    Context manager for database connections from pool
    """
    connection = None
    try:
        pool = get_connection_pool()
        connection = pool.get_connection()
        
        if connection.is_connected():
            yield connection
        else:
            raise Exception("Failed to get connection from pool")
            
    except Error as e:
        logger.error(f"Error getting connection from pool: {e}")
        raise e
    finally:
        if connection and connection.is_connected():
            connection.close()  # Returns connection to pool

def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Execute database query with error handling using connection pool
    """
    result = None
    
    try:
        with get_database_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch or query.strip().upper().startswith('SELECT'):
                # Always fetch all results to avoid 'Unread result found' error
                result = cursor.fetchall()
            else:
                # For INSERT, UPDATE, DELETE operations
                connection.commit()
                result = cursor.rowcount
                # Consume any remaining results
                while cursor.nextset():
                    pass
            
            cursor.close()
            
    except Error as e:
        logger.error(f"Database query error: {e}")
        raise e
            
    return result