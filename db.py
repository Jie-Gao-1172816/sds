"""MySQL database connectivity for Flask web app using mysqlclient."""

from flask import Flask, g
import MySQLdb

# Database connection parameters
connection_params = {}


def init_db(
    app: Flask,
    user: str,
    password: str,
    host: str,
    database: str,
    port: int = 3306,
    autocommit: bool = True,
):
    # Initialize database connection for Flask app
    connection_params["user"] = user
    connection_params["password"] = password
    connection_params["host"] = host
    connection_params["database"] = database
    connection_params["port"] = port
    connection_params["autocommit"] = autocommit

    app.teardown_appcontext(close_db)


def get_db():
    # Get MySQL database connection for current request
    if "db" not in g:
        g.db = MySQLdb.connect(**connection_params)
    return g.db


def get_cursor():
    # Get a new MySQL dictionary cursor for current request
    return get_db().cursor(cursorclass=MySQLdb.cursors.DictCursor)


def close_db(exception=None):
    # Close database connection at end of request
    db = g.pop("db", None)
    if db is not None:
        db.close()
