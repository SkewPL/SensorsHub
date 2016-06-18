#!/usr/bin/python3.4
import os
import sqlite3
import cherrypy
import json
import datetime

from jinja2 import Environment, FileSystemLoader
from libs.accounts import Accounts
from libs.sensors import Sensors
from libs.config import Config
from libs.web import WebRoot
from libs.settings import WebSettings

class Core(object):
    def __init__(self):
        # Create databse and tables
        with sqlite3.connect("db.sqlite") as conn:

            #
            # SENSORS
            # Table for sensors, each sensor has one row.
            #
            # sid - Sensor ID, must be unique
            # token - Generated string for authentication
            # title - Title of the sensor, f.eg. Outside
            # description - Description of the sensor, f.eg. ESP8266 temperature sensor
            # updated - Timestamp updated when new reading is received
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sensors("
                "sid INTEGER PRIMARY KEY AUTOINCREMENT, "
                "token TEXT, "
                "title TEXT, "
                "description TEXT, "
                "updated INTEGER, "
                "status INTEGER DEFAULT 0"
                ")")

            # FIELDS
            # Table for fields, each sensor can have multiple fields
            #
            # fid - Field ID, must be unique
            # sid - Sensor ID to which this field belong
            # name - Name of the field, f.eg. temperature
            # display_name - Human friendly name of the field, f.eg. Temperature
            # style - Icon (Font awesome name) and color (HEX) of the field, f.eg. bed#F0A
            # unit - Unit of the field, f.eg. &deg;C
            conn.execute(
                "CREATE TABLE IF NOT EXISTS fields"
                "(fid INTEGER PRIMARY KEY AUTOINCREMENT, sid INTEGER, updated INTEGER, value FLOAT, name TEXT, display_name TEXT, style TEXT, unit TEXT)")

            #
            # READINGS
            # Table for readings, each reding must specify field and sensor
            #
            # sid - Sensor ID to which this reading belong
            # fid - Field ID to which this reading belong
            # updated - When reading has been created in timestamp format
            # value - New value of the field
            conn.execute(
                """CREATE TABLE IF NOT EXISTS readings(sid INTEGER, fid INTEGER, updated INT, value FLOAT)""")

            #
            # ACCOUNTS
            # Table for accounts
            #
            # uid - User ID, must be unique
            # session - Generated string for sessions
            # user - Unique user login
            # password - Hashed password using hashlib
            # lastlogin - Timestamp updated when user logged in
            # email - User email
            conn.execute(
                """CREATE TABLE IF NOT EXISTS accounts(uid INTEGER PRIMARY KEY, session TEXT, user TEXT UNIQUE , password TEXT, lastlogin INTEGER, email TEXT)""")

        # Load config
        self.config = Config()
        self.config.load()

        # Create and read sensors from database
        self.sensors = Sensors()
        self.sensors.load()

        # Create and load accounts
        self.accounts = Accounts()

        # Create website
        env = Environment(loader=FileSystemLoader('templates'))

        def to_json(value):
            return json.dumps(value)

        env.filters["to_json"] = to_json

        def format_datetime(value, format="%d.%m.%Y %H:%M"):
            if value == None:
                return "Never"
            else:
                try:
                    return datetime.datetime.fromtimestamp(value).strftime(format)
                except TypeError:
                    return value.strftime(format)

        env.filters["strftime"] = format_datetime

        cherrypy.config.update({
            "server.socket_port": self.config.get("port", 80),
            "server.socket_host": self.config.get("host", "0.0.0.0")
        })
        cherrypy.tree.mount(WebRoot(self,env),"/", {
            "/static": {
                "tools.staticdir.root": os.getcwd(),
                "tools.staticdir.on": True,
                "tools.staticdir.dir": "static"
            }
        })
        cherrypy.tree.mount(WebSettings(self, env), "/settings", None)
        cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()
        cherrypy.engine.block()

if __name__ == "__main__":
    Core()