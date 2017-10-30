""" UTILITES """

__all__ = ['humanize_time', 'wait_threads']

import threading


def humanize_time(amount, units='seconds'):
    def process_time(amount, units):

        INTERVALS = [1, 60,
                     60 * 60,
                     60 * 60 * 24,
                     60 * 60 * 24 * 7,
                     60 * 60 * 24 * 7 * 4,
                     60 * 60 * 24 * 7 * 4 * 12,
                     60 * 60 * 24 * 7 * 4 * 12 * 100,
                     60 * 60 * 24 * 7 * 4 * 12 * 100 * 10]
        NAMES = [('second', 'seconds'),
                 ('minute', 'minutes'),
                 ('hour', 'hours'),
                 ('day', 'days'),
                 ('week', 'weeks'),
                 ('month', 'months'),
                 ('year', 'years'),
                 ('century', 'centuries'),
                 ('millennium', 'millennia')]

        result = []

        unit = map(lambda a: a[1], NAMES).index(units)
        # Convert to seconds
        amount = amount * INTERVALS[unit]

        for i in range(len(NAMES) - 1, -1, -1):
            a = amount // INTERVALS[i]
            if a > 0:
                result.append((a, NAMES[i][1 % a]))
                amount -= a * INTERVALS[i]

        return result

    rd = process_time(int(amount), units)
    cont = 0
    for u in rd:
        if u[0] > 0:
            cont += 1

    buf = ''
    i = 0
    for u in rd:
        if u[0] > 0:
            buf += "%d %s" % (u[0], u[1])
            cont -= 1

        if i < (len(rd) - 1):
            if cont > 1:
                buf += ", "
            else:
                buf += " and "

        i += 1
    if buf == '':
        return 'less than second'
    else:
        return buf


def wait_threads(npfx='U:'):
    """Wait all active threads
    :param npfx: Thread name prefix
    :type npfx: string
    """
    npfx_len = len(npfx)
    for thread in threading.enumerate():
        if thread.name[:npfx_len] == npfx:
            thread.join()
