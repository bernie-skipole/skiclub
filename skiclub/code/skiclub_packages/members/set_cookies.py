##################################
#
# These functions log a user out, and generate
# a cookie for a user on login
#
##################################

import uuid

from http import cookies

from ....skilift import FailPage, GoTo, ValidateError, ServerError, projectURLpaths

from .. import redis_ops


def logout(skicall):
    """Logs the user out by deleting the user cookie from the database, and also 
          set a cookie in the user browser to 'noaccess' which indicates logged out"""

    # When a user chooses logout - this calls responder 5003 which is of type 'SetCookies'
    # The responder calls this function, and expects the function to return a cookie object

    skicall.call_data['loggedin'] =  False
    skicall.call_data['authenticated'] = False
    skicall.call_data['role'] = ""
    if 'username' in skicall.call_data:
        del skicall.call_data['username'] 
    if 'user_id' in skicall.call_data:
        del skicall.call_data['user_id']
    if 'email' in skicall.call_data:
        del skicall.call_data['email']
    if 'member' in skicall.call_data:
        del skicall.call_data['member']
    # Remove cookie from redis database
    if 'cookie' in skicall.call_data:
        redis_ops.del_cookie(skicall.call_data['cookie'], skicall.call_data.get("rconn_1"))
        del skicall.call_data['cookie']

    # set a cookie 'project2:noaccess'
    project = skicall.project
    ck_key = project +"2"
    cki = cookies.SimpleCookie()
    cki[ck_key] = "noaccess"
    # set root project path in the cookie
    url_dict = projectURLpaths()
    cki[ck_key]['path'] = url_dict[project]

    return cki



def set_cookie(skicall):
    """set cookie for login access"""

    # After a user has tried to login and his password successfully checked then
    # this function is called from responder 5502 which is of type 'SetCookies'
    # a cookie is generated, set into the database and sent to the user browser
    # so future access is immediate when a received cookie is compared with the database cookie

    # set a cookie for cookie key 'project2'
    project = skicall.project
    user_id = skicall.call_data['user_id']
    # generate a cookie string
    ck_string = uuid.uuid4().hex
    ck_key = project +"2"
    cki = cookies.SimpleCookie()
    cki[ck_key] = ck_string
    # twelve hours expirey time
    cki[ck_key]['max-age'] = 43200
    # set root project path
    url_dict = projectURLpaths()
    cki[ck_key]['path'] = url_dict[project]
    # and set the cookie string into database
    status = redis_ops.set_cookie(ck_string, user_id, skicall.call_data.get("rconn_1"))
    if not status:
        raise FailPage(message="Unable to access redis database")
    return cki

