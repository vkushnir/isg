""" Logging Utilities """

__all__ = ['logger', 'get_logger']

import os
import sys
import logging


# setup logger object
#    CRITICAL, ERROR, WARNING, INFO, DEBUG

class LevelFilter(object):
    """Filter log records by levels"""

    def __init__(self, min_level, max_level):
        self.__min = min_level
        self.__max = max_level

    def filter(self, logRecord):
        return self.__min <= logRecord.levelno <= self.__max


def get_logger(log_name):
    """Default logger object
    :param log_name: Name logger object and files
    :type log_name: strng
    """
    log_folder = os.getenv('LOG_DIR', '/var/log/isg')

    file_formatter = logging.Formatter('%(asctime)s: %(threadName)s :%(levelname)s: %(message)s')
    stream_formatter = logging.Formatter('%(levelname)s: %(threadName)s/%(funcName)s: %(message)s')

    err_file_handler = logging.FileHandler(os.path.join(log_folder, log_name + '-error.log'))
    err_file_handler.setLevel(logging.ERROR)
    err_file_handler.setFormatter(file_formatter)
    # err_file_handler.addFilter(LevelFilter(logging.ERROR, logging.CRITICAL))
    err_stream_handler = logging.StreamHandler(sys.stderr)
    err_stream_handler.setLevel(logging.WARNING)
    err_stream_handler.setFormatter(stream_formatter)
    # err_stream_handler.addFilter(LevelFilter(logging.WARNING, logging.CRITICAL))

    std_file_handler = logging.FileHandler(os.path.join(log_folder, log_name + '.log'))
    # std_file_handler.setLevel(logging.DEBUG)
    std_file_handler.setFormatter(file_formatter)
    std_file_handler.addFilter(LevelFilter(logging.NOTSET, logging.WARNING))
    std_stream_handler = logging.StreamHandler(sys.stdout)
    # std_stream_handler.setLevel(logging.DEBUG)
    std_stream_handler.setFormatter(stream_formatter)
    std_stream_handler.addFilter(LevelFilter(logging.NOTSET, logging.INFO))

    # setup logger
    logger = logging.getLogger(log_name)
    logger.setLevel({'DEBUG': logging.DEBUG,
                     'INFO': logging.INFO,
                     'WARNING': logging.WARNING,
                     'ERROR': logging.ERROR,
                     'CRITICAL': logging.CRITICAL}.
                    get(os.getenv('LOG_LEVEL', 'DEBUG').upper(), logging.INFO))

    # add handlers
    logger.addHandler(err_file_handler)
    logger.addHandler(err_stream_handler)
    logger.addHandler(std_file_handler)
    logger.addHandler(std_stream_handler)

    return logger


logger = get_logger(os.path.basename(os.path.splitext(sys.modules['__main__'].__file__)[0]))