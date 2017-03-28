##################################
#
# This function checks the users attempt to log in
#
##################################


import random

from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops



def create_login_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Sets a hidden random number in the login form, which is only valid for four minutes
       This expires the login page, and also makes it difficult to script login calls"""

    # function database_ops.timed_random_numbers returns two random numbers
    # one valid for the current two minute time slot, one valid for the previous
    # two minute time slot.  Four sets of such random numbers are available
    # specified by argument rndset which should be 0 to 3
    # This login form uses rndset 0
    rnd1, rnd2 = database_ops.timed_random_numbers(rndset=0)
    if rnd1 is None:
        raise ServerError(message = "Database access failure")

    page_data['loginform', 'hidden_field1'] = str(rnd1)

    # When the form is submitted, the received number will be checked against another call
    # to database_ops.timed_random_numbers, and if it is equal to either of them, it is within
    # a valid timeout period.
    return



def check_login(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """The user fills in the username and password widgets on the login template page and
         then submits the data to the responder which calls this function.
         This checks username and password against the member database and raises failpage
         if username and password are not ok, if ok populates call_data"""

    # Called by responder id 5002

    call_data['loggedin'] = False
    call_data['authenticated'] = False

    username = call_data['username', 'input_text']
    password = call_data['password', 'input_text']
    if not username:
        raise FailPage(message= "Login fail: missing username", displaywidgetname='loginform')
    if not password:
        raise FailPage(message= "Login fail: missing password", displaywidgetname='loginform')
    if not database_ops.check_password(username, password):
        raise FailPage(message= "Login fail: invalid username-password", displaywidgetname='loginform')

    # password ok, get user information
    user = database_ops.get_user_from_username(username)
    # user is a tuple of (user_id, role, email, member) or None if the username is not found

    if user is None:
        # something wrong, unable to get user information
        raise FailPage(message= "Login Fail: unable to retrieve user details", displaywidgetname='loginform')
    if user[1] == 'ADMIN':
        # At this stage, the admin user may be logged in, but will not be authenticated
        # so at this point ensure his authenticated status is set to False on the database
        if not database_ops.set_authenticated(user[0], False):
            # failed to set authenticated to False
            raise FailPage(message= "Login Fail: unable to reset Admin authentication", displaywidgetname='loginform')
        # The admin user will be asked to authenticate when he tries to access an administrative function
        # The pair of PIN characters he will be asked for will be set at this stage, so it changes every time he logs in.
        # This is done by setting a random number between 1 and 6 into database
        if not database_ops.set_pair(user[0], random.randint(1,6)):
            raise FailPage(message="Login Fail: unable to access database")

    # login ok, populate call_data and return
    call_data['user_id'] = user[0]
    call_data['role'] =  user[1]
    call_data['username'] =  username
    call_data['loggedin'] =  True
