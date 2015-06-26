# denyhosts sync server
# Copyright (C) 2015 Jan-Pascal van Best <janpascal@vanbest.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor, task

_hosts_busy = set()

@inlineCallbacks
def wait_and_lock_host(host):
    try:
        logging.debug("Checking host {}".format(host))
        while host in _hosts_busy:
            logging.debug("waiting to update host {}, {} blocked now".format(host, len(_hosts_busy)))
            yield task.deferLater(reactor, 0.1, lambda _:0, 0)
        logging.debug("Blocking {}".format(host))
        _hosts_busy.add(host)
        logging.debug("Blocked {}".format(host))
    except:
        logging.debug("Exception in locking {}".format(host), exc_info=True)
    returnValue(0)

def unlock_host(host):
    try:
        logging.debug("Unblocking {}".format(host))
        _hosts_busy.remove(host)
        logging.debug("Unblocked {}".format(host))
    except:
        logging.debug("Exception in unlocking {}".format(host), exc_info=True)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
