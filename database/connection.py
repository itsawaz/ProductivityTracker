"""
MySQL Connection Pool — Thread-safe connection management.
"""

import logging
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
import config

logger = logging.getLogger(__name__)

_pool = None


def _create_database_if_not_exists():
    """
    Connect to MySQL server (without specifying a database)
    and create the productivity_tracker database if it doesn't exist.
    """
    try:
        conn = mysql.connector.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.close()
        conn.close()
        logger.info(f"Database '{config.MYSQL_DATABASE}' ensured to exist")
    except mysql.connector.Error as e:
        logger.error(f"Failed to create database: {e}")
        raise


def init_pool():
    """
    Initialize the MySQL connection pool.
    Creates the database if it doesn't exist first.
    """
    global _pool

    _create_database_if_not_exists()

    try:
        _pool = MySQLConnectionPool(
            pool_name="productivity_pool",
            pool_size=config.MYSQL_POOL_SIZE,
            pool_reset_session=True,
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            autocommit=True,
        )
        logger.info(
            f"MySQL connection pool initialized "
            f"(host={config.MYSQL_HOST}, db={config.MYSQL_DATABASE}, "
            f"pool_size={config.MYSQL_POOL_SIZE})"
        )
    except mysql.connector.Error as e:
        logger.error(f"Failed to initialize MySQL connection pool: {e}")
        raise


def get_connection():
    """
    Get a connection from the pool.
    
    Returns:
        MySQLConnection from the pool.
    
    Usage:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # ... do work ...
        finally:
            conn.close()  # returns to pool
    """
    global _pool
    if _pool is None:
        init_pool()
    return _pool.get_connection()
