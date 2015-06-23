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
import time

from twisted.internet.defer import inlineCallbacks, returnValue
from twistar.registry import Registry

import config
import models
from models import Cracker, Report

def get_cracker(ip_address):
    return Cracker.find(where=["ip_address=?",ip_address], limit=1)

@inlineCallbacks
def add_report_to_cracker(cracker, client_ip):
    now = time.time()
    report = yield Report.find(
        where=["cracker_id=? AND ip_address=?", cracker.id, client_ip],
        limit=1
    )
    if report is None:
        report = Report(ip_address=client_ip, first_report_time=now, latest_report_time=now)
        yield report.save()
        cracker.current_reports += 1
        yield report.cracker.set(cracker)
    else:
        report.latest_report_time = now
        yield report.save()
    
    cracker.total_reports += 1
    cracker.latest_time = now

    yield cracker.save()

    returnValue(report)

@inlineCallbacks
def get_qualifying_crackers(min_reports, min_resilience, previous_timestamp,
        max_crackers, latest_added_hosts):
    # Thank to Anne Bezemer for the algorithm in this function. 
    # See https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=622697
   
    # This query takes care of conditions (a) and (b)
    cracker_ids = yield Registry.DBPOOL.runQuery("""
            SELECT DISTINCT c.id, c.ip_address 
            FROM crackers c 
            JOIN reports r ON r.cracker_id=c.id
            WHERE (c.current_reports >= ?) AND 
                (c.latest_time - c.first_time >= ?)
                AND (c.latest_time >= ?)
            ORDER BY c.first_time DESC
        """, 
        [min_reports, min_resilience, previous_timestamp])
  
    if cracker_ids is None:
        returnValue([])

    # Now look for conditions (c) and (d)
    result = []
    for c in cracker_ids:
        cracker_id = c[0]
        if c[1] in latest_added_hosts:
            logging.debug("Skipping {}, just reported by client".format(c[1]))
            continue
        cracker = yield Cracker.find(cracker_id)
        logging.debug("Examining cracker:")
        logging.debug(cracker)
        reports = yield cracker.reports.get(orderby="first_report_time ASC")
        logging.debug("reports:")
        for r in reports:
            logging.debug("    "+str(r))
        if (len(reports)>=min_reports and 
            reports[min_reports-1].first_report_time >= previous_timestamp): 
            # condition (c) satisfied
            logging.debug("c")
            result.append(cracker.ip_address)
        else:
            logging.debug("checking (d)...")
            satisfied = False
            for report in reports:
                logging.debug("    "+str(report))
                if (not satisfied and 
                    report.latest_report_time>=previous_timestamp and
                    report.latest_report_time-cracker.first_time>=min_resilience):
                    logging.debug("    d1")
                    satisfied = True
                if (report.latest_report_time<=previous_timestamp and 
                    report.latest_report_time-cracker.first_time>=min_resilience):
                    logging.debug("    d2 failed")
                    satisfied = False
                    break
            if satisfied:
                logging.debug("Appending {}".format(cracker.ip_address))
                result.append(cracker.ip_address)
            else:
                logging.debug("    skipping")
        if len(result)>=max_crackers:
            break

    returnValue(result)
# From algorithm by Anne Bezemer, see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=622697
# Expiry/maintenance every hour/day:
#   remove reports with .latestreporttime older than (for example) 1 month
#     and only update cracker.currentreports
#   remove reports that were reported by what we now "reliably" know to
#     be crackers themselves
#   remove crackers that have no reports left

# TODO How memory intensive is this? Better by direct SQL queries?
@inlineCallbacks
def perform_maintenance():
    logging.info("Starting maintenance job...")
    crackers = yield Cracker.all()
    if crackers is None:
        returnValue(1)

    now = time.time()
    limit = now - config.expiry_days * 24 * 3600 
    for cracker in crackers:
        reports = yield cracker.reports.get()
        for report in reports:
            if report.latest_report_time < limit:
                logging.info("Maintenance: removing report from {} for cracker {}".format(report.ip_address, cracker.ip_address))
                cracker.current_reports -= 1
                yield report.cracker.clear()
                yield report.delete()
                yield cracker.save()
            # TODO remove reports by identified crackers
        if cracker.current_reports == 0:
            logging.info("Maintenance: removing cracker {}".format(cracker.ip_address))
            yield cracker.delete()

    returnValue(0)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
