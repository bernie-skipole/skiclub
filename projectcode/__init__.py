"""
Code for project skiclub

This package will be called by the Skipole framework to
build the project pages
"""

import os


from .. import FailPage, GoTo, ValidateError, ServerError, use_submit_list

from . import database_ops, redis_ops


# These pages can be accessed by anyone, without the need to login
# these are generally the initial responders called by a user - once
# called the responder passes the call on to further responders or templates
# which do not have to be listed here.
_UNPROTECTED_PAGES = [1,         # index
                      1002,      # CSS page
                      1004,      # CSS page
                      1006,      # CSS page
                      7001,      # Public index
                      5001,      # logon page
                      5002       # check login
                    ]

# These pages can be accessed by anyone who is logged in
_LOGGED_IN_PAGES = [5003,        # logout
                    6001,        # Members index
                    8001,        # user settings index
                    8002,        # new password
                    8003,        # new email
                    8004,        # confirm de-register oneself
                    8005         # de-register oneself
                    ]

# Any other pages, the user must be both logged in and have admin role

# Lists requests for JSON pages
_JSON_PAGES = [8004,            # de-regiser yourself
               3065,            # json_confirm_delete_user
               3075             # json_confirm_delete_member
               ]
# This list ensures code knows a JSON call has been requested


def start_project(project, projectfiles, path, option):
    """On a project being loaded, and before the wsgi service is started, this is called once,
       Note: it may be called multiple times if your web server starts multiple processes.
       This function should return a dictionary (typically an empty dictionary if this value is not used).
       Can be used to set any initial parameters, and the dictionary returned will be passed as
       'proj_data' to subsequent start_call functions."""
    # This function will be called with the following arguments
    # project - the project name
    # projectfiles - the path to the projectfiles directory
    # path - the url path to this project
    # option - an optional value given on the command line

    # checks members database exists, if not create it
    database_ops.start_database(project, projectfiles)
    # create a redis connection for miscellaneous use
    rconn_0 = redis_ops.open_redis(redis_db=0)
    # create a redis connection for logged in users
    rconn_1 = redis_ops.open_redis(redis_db=1)
    # and another for authenticated admins
    rconn_2 = redis_ops.open_redis(redis_db=2)
    # and another for user_id
    rconn_3 = redis_ops.open_redis(redis_db=3)
    # Set the organisation name into proj_data, used in page header and automated email
    return {"org_name":"Example club membership project", 'rconn_0':rconn_0, 'rconn_1':rconn_1, 'rconn_2':rconn_2, 'rconn_3':rconn_3, 'projectfiles':projectfiles}


def start_call(called_ident, skicall):
    "When a call is initially received this function is called."

    # set initial call_data values
    skicall.call_data = {
                          "called_ident":called_ident,
                          "org_name":skicall.proj_data["org_name"],
                          "authenticated":False,
                          "loggedin":False,
                          "role":"",
                          "json_requested":False,
                          "rconn_0":skicall.proj_data["rconn_0"],
                          "rconn_1":skicall.proj_data["rconn_1"],
                          "rconn_2":skicall.proj_data["rconn_2"],
                          "rconn_3":skicall.proj_data["rconn_3"],
                          "projectfiles":skicall.proj_data["projectfiles"]}

    if called_ident is None:
        # Force url not found if no called_ident
        return

    ####### If the user is logged in, populate call_data

    user = None
    if skicall.received_cookies:
        cookie_name = skicall.project + '2'
        if cookie_name in skicall.received_cookies:
            cookie_string = skicall.received_cookies[cookie_name]
            # so a recognised cookie has arrived, check redis 1 to see if the user has logged in
            rconn_1 = skicall.call_data.get("rconn_1")
            user_id = redis_ops.logged_in(cookie_string, rconn_1)
            if user_id:
                user = database_ops.get_user_from_id(user_id)
                # user is (username, role, email, member) on None on failure
                if user:
                    skicall.call_data['loggedin'] = True
                    skicall.call_data['user_id'] =  user_id
                    skicall.call_data['username'] = user[0]
                    skicall.call_data['role'] = user[1]
                    skicall.call_data['email'] = user[2]
                    skicall.call_data['member'] = user[3]
                    skicall.call_data['cookie'] = cookie_string
                    if user[1] != 'ADMIN':
                        skicall.call_data['authenticated'] = False
                    else:
                        # Is this user authenticated, check redis 2 to see if authenticated
                        rconn_2 = skicall.call_data.get("rconn_2")
                        skicall.call_data['authenticated'] = redis_ops.is_authenticated(cookie_string, rconn_2)

    ### Check the page being called
    page_num = called_ident[1]

    if page_num in _JSON_PAGES:
        skicall.call_data['json_requested'] = True
        

    ####### unprotected pages

    if page_num in _UNPROTECTED_PAGES:
        # Go straight to the page
        return called_ident

    # if user is not logged in, cannot choose any other page
    if user is None:
        if skicall.caller_ident and skicall.call_data['json_requested']:
            # divert to the home page
            skicall.page_data["JSONtoHTML"] = 'home'
            return "general_json"
        # otherwise divert to page not found
        return

    ###### So user is logged in, and call_data is populated

    # If access is required to any of these pages, can now go to page
    if page_num in _LOGGED_IN_PAGES:
        return called_ident

    ###### So for any remaining page the user must have ADMIN role
    
    # if not admin, cannot proceed
    if skicall.call_data['role'] != 'ADMIN':
        if skicall.caller_ident and skicall.call_data['json_requested']:
            # divert to the home page
            skicall.page_data["JSONtoHTML"] = 'home'
            return "general_json"
        # otherwise divert to page not found
        return

    ### All admin pages require the caller page to set caller_ident
    ### So if no caller ident redirect to home page
    if not skicall.caller_ident:
        return 'home'

    # So user is an ADMIN, is he authenticated?
    if not skicall.call_data['authenticated']:
        # unauthenticated admin allowed to call 'check_login' page to become authenticated
        if page_num == 5021:
            return called_ident
        # Unauthenticated - jump to PIN page
        if skicall.call_data['json_requested']:
            # divert to the PIN page
            skicall.page_data["JSONtoHTML"] = 'input_pin'
            return "general_json"
        return 'input_pin'

    # So user is both a logged in Admin user, and authenticated,

    # An authenticated user should never call pages to become authenticated, as he is already there
    if (page_num == 5021) or (page_num == 5515):
        return 'home'

    # can go to any remaining page
    return called_ident


@use_submit_list
def submit_data(skicall):
    """This function is called when a Responder wishes to submit data for processing in some manner
       For two or more submit_list values, the decorator ensures the matching function is called instead"""

    raise FailPage("submit_list string not recognised")


# each template page has a short string set in the page header
_HEADER_TEXT = { 2001 : "Home Page",
                 3501: "Setup Page",
                 3510: "Add User Page",
                 3520: "Server Settings Page",
                 3540: "Edit Users Page",
                 3610: "Edit User Page",
                 3620: "Set Admin user PIN",
                 5501: "Login Page",
                 5510: "Logged In",
                 5520: "PIN Required",
                 5530: "Authenticated",
                 5540: "PIN Fail",
                 6501: "Members Page",
                 7501: "Public Page",
                 8501: "Your Settings Page",
                 8601: "New PIN",
                 9501: "Tests Page"
               }


def end_call(page_ident, page_type, skicall):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""

    if page_type != "TemplatePage":
        return

    message_string = database_ops.get_all_messages()
    if message_string:
        skicall.page_data['navigation', 'messages', 'para_text'] = message_string

    page_num = page_ident[1]

    skicall.page_data['header','headtitle','tag_text'] = skicall.proj_data["org_name"]
    skicall.page_data['header', 'headpara', 'para_text']  = _HEADER_TEXT[page_num]
    if skicall.call_data['loggedin']:
        skicall.page_data['header', 'user', 'para_text']  = "Logged in : " + skicall.call_data['username']
        skicall.page_data['header', 'user', 'show']  = True

    ### set the page left navigation buttons ###

    # All template pages apart from home have a home link
    # All template pages apart from public have a public link
    if page_num == 2001:
        nav_buttons = [['public','Public', True, '']]
    elif page_num == 7501:
        nav_buttons = [['home','Home', True, '']]
    else:
        nav_buttons = [['home','Home', True, ''], ['public','Public', True, '']]

    if not skicall.call_data['loggedin']:
        # user is not logged in
        if page_num != 5501:
            # If not already at the login page, then add a Login option to nav buttons
            nav_buttons.append( ['login','Login', True, ''])
        # set these nav_buttons into the widget and return
        skicall.page_data['navigation', 'navbuttons', 'nav_links'] = nav_buttons
        return

    ## user is logged in ##

    # logged in users have access to membership pages
    if page_num != 6501:
        nav_buttons.append( ['members','Members', True, ''])
    # and to your settings page
    if page_num != 8501:
        nav_buttons.append( ['usersettings','Your Settings', True, ''])
    # user has logout option
    nav_buttons.append( ['logout','Logout', True, ''])

    # logged in administrators have access to further pages
    if skicall.call_data['role'] == 'ADMIN':
        # admin users have access to setpin,  setup page and tests page
        if page_num != 8601:
            nav_buttons.append( ['setpin','New PIN', True, ''])
        if page_num != 3501:
            nav_buttons.append( ['setup','Setup', True, ''])
        if page_num != 9501:
            nav_buttons.append( ['tests','Tests', True, ''])

    # set these nav_buttons into the widget
    skicall.page_data['navigation', 'navbuttons', 'nav_links'] = nav_buttons

    return

