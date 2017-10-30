""" RADIUS Utilities """

__all__ = ['raddict', 'get_client', 'get_dictionary', 'add_message_authenticator',
           'session_info', 'disconnect_user', 'subscriber_services']

import os
import hmac
import struct
from pyrad.client import Client
from pyrad import dictionary
from pyrad import packet
from log import logger


def get_dictionary(raddicts=None):
    """Return RADIUS dictionary
    :param raddicts: List dictionary files if None then get all files from dictionary folder
    :type raddicts: sequence of strings or files
    :return: Dictionary object
    :rtype: pyrad.dictionary.Dictionary
    """
    if raddicts is None:
        raddict_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dictionary')
        raddict = dictionary.Dictionary(
            *[os.path.join(raddict_folder, raddict_file) for raddict_file in os.listdir(raddict_folder)])
    else:
        raddict = dictionary.Dictionary(raddicts)
    return raddict


def get_client(server, port, secret):
    """Get pyrad client class.
    :param server: IP Address of NAS Server
    :param port: Port of CoA Server
    :param secret: Client secret
    :type server: string
    :type port: integer
    :type secret: string
    :return: Return basic RADIUS client
    :rtype: pyrad.Client
    """
    return Client(server=server, coaport=port, authport=port, acctport=port,
                  secret=secret, dict=raddict)


def add_message_authenticator(packet):
    """Calculate Message-Authenticator and add to Request Packet
    :param packet: RADIUS attributes
    :type packet: pyrad.packet.Packet
    """
    packet.authenticator = packet.CreateAuthenticator()
    hmac_obj = hmac.new(packet.secret)
    hmac_obj.update(struct.pack("B", packet.code))
    hmac_obj.update(struct.pack("B", packet.id))

    # request attributes
    packet.AddAttribute("Message-Authenticator", 16 * "\x00")
    attrs = packet._PktEncodeAttributes()

    # Length
    flen = 4 + 16 + len(attrs)
    hmac_obj.update(struct.pack(">H", flen))
    hmac_obj.update(16 * "\x00")  # all zeros Authenticator in calculation
    hmac_obj.update(attrs)
    del packet[80]
    packet.AddAttribute("Message-Authenticator", hmac_obj.digest())


def session_info(user_name, acct_session_id, client):
    """Get subscriber session info
    :param user_name: Subscriber User_Name
    :param acct_session_id: Subscriber Session ID
    :param client: Basic RADIUS client
    :type user_name: string
    :type acct_session_id: basestring
    :type client: pyrad.Client object
    :return: Subscriber Session RADIUS Attributes or None if fail
    :rtype: pyrad.packet.Packet
    """
    logger.debug("get user %s@%s[%s] status.", user_name, client.server, acct_session_id)

    req = client.CreateCoAPacket(User_Name=user_name, Acct_Session_Id=acct_session_id,
                                 Cisco_AVPair="subscriber:command=session-query")
    add_message_authenticator(req)

    try:
        reply = client.SendPacket(req)
    except:
        logger.error("NAS:%s CoA session-query error!!!", client.server)
        return None
    # :TODO Sometime cisco did't return Framed-IP-Address, find and fix and att test
    # logger.debug("Framed-IP-Address:%s", reply['Framed-IP-Address'])
    return reply


def disconnect_user(user_name, acct_session_id, client):
    """Terminate online session
    :param user_name: Subscriber User_Name
    :param acct_session_id: Subscriber Session ID
    :param client: Basic RADIUS client
    :type user_name: string
    :type acct_session_id: basestring
    :type client: pyrad.Client
    :return: RADIUS Attributes or None if fail
    :rtype: pyrad.packet.Packet
    """
    logger.debug("termnate user %s@%s[%s]", user_name, client.server, acct_session_id)

    req = client.CreateAcctPacket(code=packet.DisconnectRequest, User_Name=user_name, Acct_Session_Id=acct_session_id)
    try:
        reply = client.SendPacket(req)
    except:
        logger.error("NAS:%s Disconnect-request error!!!", client.server)
        return None
    return reply


def subscriber_services(mode, user_name, acct_session_id, services, client):
    """Activate/Deactivate subscriber services
    :param mode: 'activate' or 'deactivate'
    :param user_name: Subscriber User_Name
    :param acct_session_id: Subscriber Session ID
    :param services: Services required for activation or deactivation
    :param client: Basic RADIUS client
    :type mode: string
    :type user_name: string
    :type acct_session_id: string
    :type services: list
    :type client: pyrad.Client
    :return: RADIUS Attributes or None if fail
    :rtype: pyrad.packet.Packet
    """
    logger.debug("%s:%s for user %s@%s[%s]", mode, str(services), user_name, client.server, acct_session_id)
    result = True
    for svc in services:
        req = client.CreateCoAPacket(User_Name=user_name, Acct_Session_Id=acct_session_id,
                                     Cisco_AVPair=["subscriber:command=" + mode + "-service"] +
                                                  ["subscriber:service-name=" + svc])
        add_message_authenticator(req)
        try:
            reply = client.SendPacket(req)
        except:
            logger.critical("NAS:%s CoA %s-service %s error!!!", client.server, mode, svc)
            return False
        result = result and reply.code == packet.CoAACK
    return result
    # :TODO CISCO ignore additional service-name
    # req = client.CreateCoAPacket(User_Name=user_name, Acct_Session_Id=acct_session_id,
    #                              Cisco_AVPair=["subscriber:command=" + mode + "-service"] + [
    #                                  "subscriber:service-name=" + svc for svc in services])


def update_subscriber_services(user_name, acct_session_id, session, services, client):
    """Update subscriber active services according given list
    :param user_name: Subscriber User_Name
    :param acct_session_id: Subscriber Session ID
    :param session: Subscriber session info
    :param services: Services required set
    :param client: Basic RADIUS client
    :type user_name: string
    :type acct_session_id: string
    :type session: pyrad.packet.Packet
    :type services: list
    :type client: pyrad.Client
    :return: True or False
    :rtype: bool
    """
    session_services = [svc.split(';')[0][2:] for svc in session['Cisco-Account-Info'] if svc[:2] == 'N1']
    logger.debug("update services from %s to %s for user %s@%s[%s]", str(session_services), str(services),
                 user_name, client.server, acct_session_id)

    # new_services = [svc for svc in services if svc not in session_services]
    # old_services = [svc for svc in session_services if svc not in services]

    result = True
    if len(session_services) > 0 and \
            not subscriber_services('deactivate', user_name, acct_session_id, session_services, client):
        logger.error("can't deactivate services:%s", str(session_services))
        result = False

    if len(services) > 0 and \
            not subscriber_services('activate', user_name, acct_session_id, services, client):
        logger.error("can't activate services:%s", str(services))
        result = False
    return result


raddict = get_dictionary()
