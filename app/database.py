""" DATABASE Utilities """

__all__ = ['set_speed', 'get_services']

import os
import sys
import cx_Oracle
from log import logger

# create oracle connection pool
try:
    SessionPool = cx_Oracle.SessionPool(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'),
                                        dsn="{!s}/{!s}".format(os.getenv('DB_ADDRESS'), os.getenv('DB_NAME')),
                                        min=int(os.getenv('DB_MIN')), max=int(os.getenv('DB_MAX')),
                                        increment=int(os.getenv('DB_INC')), threaded=True)
except:
    logger.critical("Can't create database SessionPool !!!")
    sys.exit(1)


def set_speed(user_name, new_speed, tariff):
    """Set new radgout for user.
    :param user_name: User name to change radgroup
    :param new_speed: New user speed
    :param tariff: User tariff???
    :type user_name: string
    :type new_speed: string
    :type tariff: integer
    :return: True or False
    :rtype: bool
    """
    logger.debug("set speed %s:%s for user %s", new_speed, tariff, user_name)

    with SessionPool.acquire() as con:
        cur = con.cursor()
        code = cur.var(cx_Oracle.NUMBER)
        message = cur.var(cx_Oracle.STRING)
        try:
            cur.callproc('RADIUS.CHANGE_USER_SPEED', (user_name, new_speed, tariff, code, message))
        except:
            logger.critical("database error!!!")
            return False
    rcode = code.getvalue()
    if rcode != 0:
        logger.error("can't set speed %s:%s", rcode, message.getvalue())
        return False
    return True


def get_services(user_group):
    """Get services from radgroup
    :param user_group: User group with ISG services
    :type user_group: string
    :return: list of radgroup services
    :rtype: list
    """
    logger.debug("get services from usergroup %s", user_group)

    with SessionPool.acquire() as con:
        cur = con.cursor()
        try:
            cur.execute("""SELECT LTRIM(VALUE, 'A')
                FROM RADIUS.RADGROUPREPLY r
                    WHERE r.GROUPNAME = :grp
                    AND r.VALUE LIKE '%SVC%'""", grp=user_group)
        except:
            logger.critical("database error!!!")
            return []
        services = [svc[0] for svc in cur.fetchall()]
        logger.debug("%s: %s", user_group, str(services))
    return services
