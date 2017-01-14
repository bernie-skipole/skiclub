##################################
#
# These functions log a user out, and generate
# a cookie for a user on login
#
##################################

import uuid

from http import cookies

from ....skilift import FailPage, GoTo, ValidateError, ServerError, projectURLpaths

from .. import database_ops


def logout(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Logs the user out by deleting the user cookie from the database, and also 
          set a cookie in the user browser to 'noaccess' which indicates logged out"""

    # When a user chooses logout - this calls responder 5003 which is of type 'SetCookies'
    # The responder calls this function, and expects the function to return a cookie object

    call_data['loggedin'] =  False
    call_data['authenticated'] = False
    if 'username' in call_data:
        del call_data['username'] 
    # If user_id given remove cookie from user in database
    if 'user_id' in call_data:
        user_id = call_data['user_id']
        database_ops.del_cookie(user_id)
        del call_data['user_id']

    # set a cookie 'project2:noaccess'
    project = call_data['project']
    ck_key = project +"2"
    cki = cookies.SimpleCookie()
    cki[ck_key] = "noaccess"
    # set root project path in the cookie
    url_dict = projectURLpaths()
    cki[ck_key]['path'] = url_dict[project]

    return cki



def set_cookie(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """set cookie for login access"""

    # After a user has tried to login and his password successfully checked then
    # this function is called from responder 5502 which is of type 'SetCookies'
    # a cookie is generated, set into the database and sent to the user browser
    # so future access is immediate when a received cookie is compared with the database cookie

    # set a cookie for cookie key 'project2'
    project = call_data['project']
    user_id = call_data['user_id']
    # generate a cookie string
    ck_string = str(user_id) + '_' + uuid.uuid4().hex
    ck_key = project +"2"
    cki = cookies.SimpleCookie()
    cki[ck_key] = ck_string
    # twelve hours expirey time
    cki[ck_key]['max-age'] = 43200
    # set root project path
    url_dict = projectURLpaths()
    cki[ck_key]['path'] = url_dict[project]
    # and set the cookie string into database
    if not database_ops.set_cookie(user_id, ck_string):
        raise FailPage(message="Unable to access database")
    return cki

