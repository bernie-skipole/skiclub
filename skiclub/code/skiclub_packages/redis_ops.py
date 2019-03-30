

import random

try:
    import redis
except:
    _REDIS_AVAILABLE = False
else:
    _REDIS_AVAILABLE = True


from skipole import FailPage, GoTo, ValidateError, ServerError

from . import cfg


def open_redis(redis_db=0):
    "Returns a connection to the redis database"

    if not _REDIS_AVAILABLE:
        raise FailPage(message = "redis module not loaded")

    rconn = None

    # redis server settings from cfg.py
    redis_ip, redis_port, redis_auth = cfg.get_redis()

    if not redis_ip:
        raise FailPage("Redis service not available")

    # create a connection to the redis data logging server
    try:
        rconn = redis.StrictRedis(host=redis_ip, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
    except:
        raise FailPage("Redis service not available")

    if rconn is None:
        raise FailPage("Redis service not available")

    return rconn


############################################################
#
# The following deals with cookies and user logged in status
#
############################################################


def logged_in(cookie_string, rconn=None):
    """Check for a valid cookie, if logged in, return user_id
       If not, return None. If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 1"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return

    if rconn is None:
        return

    if (not cookie_string) or (cookie_string == "noaccess"):
        return
    try:
        if not rconn.exists(cookie_string):
            return
        user_info = rconn.lrange(cookie_string, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number, added to input pin form and checked on submission
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        user_id = int(user_info[0].decode('utf-8'))
        # and update expire after two hours
        rconn.expire(cookie_string, 7200)
    except:
        return
    return user_id


def set_cookie(cookie_string, user_id, rconn=None):
    """Return True on success, False on failure, if rconn is None, it is created.
       If given rconn should connect to redis_db 1"""
    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return False

    if rconn is None:
        return False

    if (not  user_id) or (not cookie_string):
        return False

    # with cookie string as key, set value as a list of [user_id, random_number]
    try:
        if rconn.exists(cookie_string):
            # cookie already delete it
            rconn.delete(cookie_string)
            # and return False, as this should not happen
            return False
        # set the cookie into the database
        rconn.rpush(cookie_string, str(user_id), str(random.randint(10000000, 99999999)), str(random.randint(1,6)))
        rconn.expire(cookie_string, 7200)
    except:
        return False
    return True



def del_cookie(cookie_string, rconn=None):
    """Return True on success, False on failure, if rconn is None, it is created.
       If given rconn should connect to redis_db 1"""
    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return False

    if rconn is None:
        return False

    if not cookie_string:
        return False
    try:
        rconn.delete(cookie_string)
    except:
        return False
    return True


def set_rnd(cookie_string, rconn=None):
    """Sets a random number against the cookie, return the random number on success,
       None on failure,
       if rconn is None, it is created.
       If given rconn should connect to redis_db 1"""
    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return

    if rconn is None:
        return

    if not cookie_string:
        return

    rnd = random.randint(10000000, 99999999)

    # with cookie string as key, set a random_number
    try:
        if not rconn.exists(cookie_string):
            return
        # set the random number into the database
        rconn.lset(cookie_string, 1, str(rnd))
    except:
        return
    return rnd


def get_rnd(cookie_string, rconn=None):
    """Gets the saved random number from the cookie, return the random number on success,
       None on failure.
       Once called, it creates a new random number to store in the database,
       so the number returned is then lost from the database.
       If rconn is None, it is created.
       If given rconn should connect to redis_db 1"""
    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return

    if rconn is None:
        return

    if not cookie_string:
        return

    # with cookie string as key, get and set a random_number
    try:
        if not rconn.exists(cookie_string):
            return
        user_info = rconn.lrange(cookie_string, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        rnd = int(user_info[1].decode('utf-8'))
        # after obtaining rnd, insert a new one
        newrnd = random.randint(10000000, 99999999)
        rconn.lset(cookie_string, 1, str(newrnd))
    except:
        return
    return rnd


def get_pair(cookie_string, rconn=None):
    """Gets the saved pair random number from the cookie, return it on success,
       None on failure.
       If rconn is None, it is created.
       If given rconn should connect to redis_db 1"""
    if rconn is None:
        try:
            rconn = open_redis(redis_db=1)
        except:
            return

    if rconn is None:
        return

    if not cookie_string:
        return

    # with cookie string as key, get the pair number
    try:
        if not rconn.exists(cookie_string):
            return
        user_info = rconn.lrange(cookie_string, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        pair = int(user_info[2].decode('utf-8'))
    except:
        return
    return pair


def is_authenticated(cookie_string, rconn=None):
    """Check for a valid cookie, if logged in, return True
       If not, return False. If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 2"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=2)
        except:
            return False

    if rconn is None:
        return False

    if (not cookie_string) or (cookie_string == "noaccess"):
        return False
    try:
        if rconn.exists(cookie_string):
            # key exists, and update expire after ten minutes
            rconn.expire(cookie_string, 600)
        else:
            return False
    except:
        return False
    return True


def set_authenticated(cookie_string, user_id, rconn=None):
    """Sets cookie into redis db2 as key, with [user_id,...] as value
       If successfull return True, if not return False.
       If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 2"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=2)
        except:
            return False

    if rconn is None:
        return False

    if (not  user_id) or (not cookie_string):
        return False
    try:
        if rconn.exists(cookie_string):
            # already authenticated, delete it
            rconn.delete(cookie_string)
            # and return False, as this should not happen
            return False
        # set the cookie into the database
        rconn.rpush(cookie_string, str(user_id))
        rconn.expire(cookie_string, 600)
    except:
        return False
    return True


##################################################
#
# count of pin failures for a user, stored in db 3
#
##################################################



def increment_try(user_id, rconn=None):
    """creates an incrementing count against the user_id
       which expires after one hour
       If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 3"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=3)
        except:
            return

    if rconn is None:
        return

    str_user_id = str(user_id)

    # increment and reset expire
    tries = rconn.incr(str_user_id)
    rconn.expire(str_user_id, 3600)
    return int(tries)


def get_tries(user_id, rconn=None):
    """Gets the count against the user_id
       If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 3"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=3)
        except:
            return

    if rconn is None:
        return

    str_user_id = str(user_id)

    if not rconn.exists(str_user_id):
        # No count, equivalent to 0
        return 0

    tries = rconn.get(str_user_id)
    return int(tries)


def clear_tries(user_id, rconn=None):
    """Clears the count to zero against the user_id
       If rconn is None, a new connection will be created.
       If given rconn should connect to redis_db 3"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=3)
        except:
            return

    if rconn is None:
        return

    str_user_id = str(user_id)

    rconn.set(str_user_id, 0)
    return




################################################
#
# Two timed random numbers, stored in db 0
#
################################################

def two_min_numbers(rndset, rconn=None):
    """returns two random numbers
       one valid for the current two minute time slot, one valid for the previous
       two minute time slot.  Four sets of such random numbers are available
       specified by argument rndset which should be 0 to 3
       If given rconn should connect to redis_db 0"""

    # limit rndset to 0 to 3
    if rndset not in (0,1,2,3):
        return None, None

    # call timed_random_numbers with timeslot of two minutes in seconds
    return timed_random_numbers(rndset, 120, rconn)



def timed_random_numbers(rndset, timeslot, rconn=None):
    """returns two random numbers
       one valid for the current time slot, one valid for the previous
       time slot.  Multiple sets of such random numbers are available
       specified by argument rndset which should be an integer.
       If given rconn should connect to redis_db 0"""

    if rconn is None:
        try:
            rconn = open_redis(redis_db=0)
        except:
            return None, None

    if rconn is None:
        return None, None

    key = "rndset_" + str(rndset)
    now = rconn.time()[0]     # time in seconds

    try:

        if not rconn.exists(key):
            rnd1 = random.randint(10000000, 99999999)
            rnd2 = random.randint(10000000, 99999999)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2

        start, rnd1, rnd2 = rconn.lrange(key, 0, -1)
        start = int(start.decode('utf-8'))
        rnd1 = int(rnd1.decode('utf-8'))
        rnd2 = int(rnd2.decode('utf-8'))

        if now < start + timeslot:
            # now is within timeslot of start time, so current random numbers are valid
            return rnd1, rnd2

        elif now < start + timeslot + timeslot:
            # now is within twice the timeslot of start time, so rnd1 has expired. but rnd2 is valid
            # set rnd2 equal to rnd1 and create new rnd1
            rnd2 = rnd1
            rnd1 = random.randint(10000000, 99999999)
            rconn.delete(key)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2

        else:
            # now is greater than twice timeslot after start time, ro rnd1 and rnd2 are invalid, create new ones
            rnd1 = random.randint(10000000, 99999999)
            rnd2 = random.randint(10000000, 99999999)
            rconn.delete(key)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2
    except:
        pass

    return None, None


