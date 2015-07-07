from dh_syncserver import config
from dh_syncserver import models
from dh_syncserver import database

from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks, returnValue

from twistar.registry import Registry

class TestBase(unittest.TestCase):
    @inlineCallbacks
    def setUp(self):
        Registry.DBPOOL = adbapi.ConnectionPool("sqlite3", "unittest.sqlite")
        Registry.register(models.Cracker, models.Report)
        # Kludge to get evolve_database to work
        config.dbtype = "sqlite3"
        yield database.clean_database()


