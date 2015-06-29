#    denyhosts sync server
#    Copyright (C) 2015 Jan-Pascal van Best <janpascal@vanbest.org>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import logging
import sys

def _get(config, section, option, default=None):
    try:
        result = config.get(section, option)
    except ConfigParser.NoOptionError:
        result = default
    return result

def _getint(config, section, option, default=None):
    try:
        result = config.getint(section, option)
    except ConfigParser.NoOptionError:
        result = default
    return result

def _getboolean(config, section, option, default=None):
    try:
        result = config.getboolean(section, option)
    except ConfigParser.NoOptionError:
        result = default
    return result

def _getfloat(config, section, option, default=None):
    try:
        result = config.getfloat(section, option)
    except ConfigParser.NoOptionError:
        result = default
    return result

def read_config(filename):
    global dbtype, dbparams
    global maintenance_interval, expiry_days
    global max_reported_crackers
    global logfile
    global loglevel
    global listen_port
    global legacy_server
    global legacy_frequency
    global legacy_threshold, legacy_resiliency

    _config = ConfigParser.SafeConfigParser()
    _config.read(filename)

    dbtype = _get(_config, "database", "type", "sqlite3")
    if dbtype not in ["sqlite3","MySQLdb"]:
        print("Database type {} not supported, exiting".format(dbtype))
        sys.exit()

    dbparams = {
        key: value 
        for (key,value) in _config.items("database") 
        if key != "type"
    }
    if dbtype=="sqlite3":
        dbparams["check_same_thread"] = False
        dbparams["cp_max"] = 1
        if "database" not in dbparams:
            dbparams["database"] = "/var/lib/dh_syncserver/denyhosts.sqlite"
    if "cp_max" in dbparams:
        dbparams["cp_max"] = int(dbparams["cp_max"])
    if "cp_min" in dbparams:
        dbparams["cp_min"] = int(dbparams["cp_min"])
    if "port" in dbparams:
        dbparams["port"] = int(dbparams["port"])
    if "connect_timeout" in dbparams:
        dbparams["connect_timeout"] = float(dbparams["connect_timeout"])
    if "timeout" in dbparams:
        dbparams["timeout"] = float(dbparams["timeout"])

    maintenance_interval = _getint(_config, "maintenance", "interval_seconds", 3600)
    expiry_days = _getfloat(_config, "maintenance", "expiry_days", 30)

    max_reported_crackers = _getint(_config, "sync", "max_reported_crackers", 50)
    listen_port = _getint(_config, "sync", "listen_port", 9911)
    legacy_server = _get(_config, "sync", "legacy_server", "http://xmlrpc.denyhosts.net:9911")
    legacy_frequency = _getint(_config, "sync", "legacy_frequency", 300)
    legacy_threshold = _getint(_config, "sync", "legacy_threshold", 3)
    legacy_resiliency = _getint(_config, "sync", "legacy_resiliency", 18000)

    logfile = _get(_config, "logging", "logfile", "/var/log/dh-syncserver.log")
    loglevel = _get(_config, "logging", "loglevel", "INFO")
    try:
        loglevel = int(loglevel)
    except ValueError:
        try:
            loglevel = logging.__dict__[loglevel]
        except KeyError:
            print("Illegal log level {}".format(loglevel))
            loglevel = logging.INFO
