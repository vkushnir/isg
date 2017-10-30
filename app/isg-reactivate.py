#!/usr/bin/python2
"""
    This python module is used for ISG services BiKaDa

    Written by : Vladimir Kushnir
    Created date: 24.10.2017
    Last modified: 24.10.2017
    Tested with : Python 2.7.12
"""

__version__ = '0.3'
__copyright__ = "Vladimir Kushnir aka Kvantum i(c)2017"

import os
import sys
import time
import threading
import radius as coa
import database as db
from utilites import humanize_time, wait_threads
from pyrad import packet
from log import logger


def isg_thread(user_name, acct_session_id, radgroup, client):
    """ Thread for main job.
    :param user_name: Subscriber User_Name
    :param acct_session_id: Subscriber Session ID
    :param radgroup: New user RADIUS group
    :param client: Basic RADIUS client
    :type user_name: string
    :type acct_session_id: string
    :type radgroup: string
    :type client: pyrad.Client
    """
    logger.info("start thread for %s@%s", user_name, client.server)

    # Get User session info
    if client.server is not None:
        session = coa.session_info(user_name, acct_session_id, client)
        if session is None:
            logger.critical("can't connect to NAS:%s", client.server)
        elif session.code == packet.CoANAK:
            logger.warning("can't find active user %s@%s[%s]", user_name, client.server, acct_session_id)
        elif session.code == packet.CoAACK:
            services = db.get_services(radgroup)
            if not coa.update_subscriber_services(user_name, acct_session_id, session, services, client):
                logger.error("can't update user services!")
                # TODO: Disconnect user casuse CISCO 7200 warm reboot, fix it before use POD packets
                # disconnect = coa.disconnect_user(user_name, acct_session_id, client, logger)
                # if disconnect is not None and disconnect.code == packet.CoANAK:
                #    logger.critical("can't disconnect user!")
                #    return None


# MAIN
def main():
    """MAIN Program."""
    start_time = time.time()
    max_threads = int(os.getenv('THREADS_MAX'))
    nas_secret = os.getenv('RADIUS_SECRET')
    coa_port = int(os.getenv('RADIUS_COAPORT'))

    # TODO: Make threading.Timer to check if script working too long or stop Docker service by timeout
    # TODO: Put data in to SQLite and scan it in paralel mode
    with db.SessionPool.acquire() as con:
        cur = con.cursor()
        cur_time = time.time()
        cur.execute("""
                SELECT "SC_IN", "SESSIONID", "NEW_RADGROUP", "USERNAME", "SRC_MESSAGE", "SRC_CODE", "NASIPADDRESS"
                FROM RADIUS.V_ISG
                WHERE sessionid is not null""")
        logger.debug("Data recived in %s", humanize_time(time.time() - cur_time))

        for sc_in, sessionid, new_radgroup, username, src_message, src_code, nasipaddress in cur:
            logger.debug(
                "SESSIONID:%s, NEW_RADGROUP:%s, USERNAME:%s, SRC_MESSAGE:'%s', SRC_CODE:%s, NASIPADDRESS:%s",
                sessionid, new_radgroup, username, src_message, src_code, nasipaddress)

            coa_client = coa.get_client(nasipaddress, coa_port, nas_secret)

            if max_threads > 0:
                while threading.activeCount() > max_threads:
                    time.sleep(0.1)
                threading.Thread(target=isg_thread,
                                 args=(username, sessionid, new_radgroup, coa_client),
                                 name="U:" + username).start()
            else:
                isg_thread(username, sessionid, new_radgroup, coa_client)
        logger.info('Finish in %s', humanize_time(time.time() - start_time))


if __name__ == '__main__':
    start_time = time.time()
    logger.info('START')
    exit_status = int(not main())
    wait_threads()
    logger.info('END IN:%s', humanize_time(time.time() - start_time))
    sys.exit(exit_status)
