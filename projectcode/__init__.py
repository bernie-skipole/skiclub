"""
Code for project skiclub

This package will be called by the Skipole framework to
build the project pages
"""

import os


from ...skilift import FailPage, GoTo, ValidateError, ServerError

from . import public, members, admin, database_ops


# These pages can be accessed by anyone, without the need to login
# these are generally the initial responders called by a user - once
# called the responder passes the call on to further responders or templates
# which do not have to be listed here.
_UNPROTECTED_PAGES = [1,         # index
                      1001,      # CSS page
                      7001,      # Public index
                      5001,      # logon page
                      5002       # check login
                    ]

# These pages can be accessed by anyone who is logged in
_LOGGED_IN_PAGES = [5003,        # logout
                    6001,        # Members index
                    8001,        # user settings index
                    8002,        # new password
                    8003         # new email
                    ]

# Any other pages, the user must be both logged in and have admin role

def start_project(project, projectfiles, path, option):
    """On a project being loaded, and before the wsgi service is started, this is called once,
       and should return a dictionary (typically an empty dictionary if this value is not used).
       This function can be used to set any initial parameters, and the dictionary returned will
       be passed as 'proj_data' to subsequent start_call functions."""
    # This function will be called with the following arguments
    # project - the project name
    # projectfiles - the path to the projectfiles/projectname directory
    # path - the url path to this project
    # option - an optional value given on the command line

    # checks members database exists, if not create it
    database_ops.start_database(project, projectfiles)
    # Set the organisation name into proj_data, used in page header and automated email
    proj_data = {"org_name":"Example club membership project"}
    return proj_data


def start_call(environ, path, project, called_ident, caller_ident, received_cookies, ident_data, lang, option, proj_data):
    "When a call is initially received this function is called."

    # set initial call_data values
    page_data = {}
    call_data = { "project":project,
                               "org_name":proj_data["org_name"],
                               "authenticated":False,
                               "loggedin":False,
                               "role":""}

    if called_ident is None:
        # Force url not found if no called_ident
        return called_ident, call_data, page_data, lang

    ####### If the user is logged in, populate call_data

    if received_cookies:
        user = database_ops.logged_in(received_cookies)
    else:
        user = None

    # user is (user_id, username, role, authenticated) if logged in or None

    if user:
        call_data['loggedin'] = True
        call_data['user_id'] =  user[0]
        call_data['username'] = user[1]
        call_data['role'] =  user[2]
        call_data['authenticated'] = user[3]

    ### Check the page being called
    page_num = called_ident[1]

    ####### unprotected pages

    if page_num in _UNPROTECTED_PAGES:
        # Go straight to the page
        return called_ident, call_data, page_data, lang

    # if user not logged in, cannot choose any other page
    # So divert to page not found
    if user is None:
        return None,  call_data, page_data, lang

    ###### So user is logged in, and call_data is populated

    # If access is required to any of these pages, can now go to page
    if page_num in _LOGGED_IN_PAGES:
        return called_ident, call_data, page_data, lang

    ###### So for any remaining page the user must have ADMIN role

    # if not admin, send to page not found
    if call_data['role'] != 'ADMIN':
        return None, call_data, page_data, lang

    ### All admin pages require the caller page to set caller_ident
    ### So if no caller ident redirect to home page
    if not caller_ident:
        return 'home',  call_data, page_data, lang

    # So user is an ADMIN, is he authenticated?
    if not call_data['authenticated']:
        # unauthenticated admin allowed to call 'check_login' page to become authenticated
        if page_num == 5021:
            return called_ident, call_data, page_data, lang
        # Unauthenticated call - jump to PIN page
        call_data['called_ident'] = called_ident
        return (project,5515), call_data, page_data, lang

    # So user is both a logged in Admin user, and authenticated,

    # An authenticated user should never call pages to become authenticated, as he is already there
    if (page_num == 5021) or (page_num == 5515):
        return 'home',  call_data, page_data, lang

    # can go to any remaining page
    return called_ident, call_data, page_data, lang


def submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "This function is called when a Responder wishes to submit data for processing in some manner"

    # depending on the first item in submit list, send the call to a sub package

    if submit_list and (submit_list[0] == 'public'):
        return public.submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    if submit_list and (submit_list[0] == 'members'):
        return members.submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    if submit_list and (submit_list[0] == 'admin'):
        return admin.submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

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


def end_call(page_ident, page_type, call_data, page_data, proj_data, lang):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""
    if page_type != "TemplatePage":
        return

    message_string = database_ops.get_all_messages()
    if message_string:
        page_data['navigation', 'messages', 'para_text'] = message_string

    page_num = page_ident[1]

    page_data['header','headtitle','tag_text'] = proj_data["org_name"]
    page_data['header', 'headpara', 'para_text']  = _HEADER_TEXT[page_num]
    if call_data['loggedin']:
        page_data['header', 'user', 'para_text']  = "Logged in : " + call_data['username']
        page_data['header', 'user', 'show']  = True

    ### set the page left navigation buttons ###

    # All template pages apart from home have a home link
    # All template pages apart from public have a public link
    if page_num == 2001:
        nav_buttons = [['public','Public', True, '']]
    elif page_num == 7501:
        nav_buttons = [['home','Home', True, '']]
    else:
        nav_buttons = [['home','Home', True, ''], ['public','Public', True, '']]

    if not call_data['loggedin']:
        # user is not logged in
        if page_num != 5501:
            # If not already at the login page, then add a Login option to nav buttons
            nav_buttons.append( ['login','Login', True, ''])
        # set these nav_buttons into the widget and return
        page_data['navigation', 'navbuttons', 'nav_links'] = nav_buttons
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
    if call_data['role'] == 'ADMIN':
        # admin users have access to setpin,  setup page and tests page
        if page_num != 8601:
            nav_buttons.append( ['setpin','New PIN', True, ''])
        if page_num != 3501:
            nav_buttons.append( ['setup','Setup', True, ''])
        if page_num != 9501:
            nav_buttons.append( ['tests','Tests', True, ''])

    # set these nav_buttons into the widget
    page_data['navigation', 'navbuttons', 'nav_links'] = nav_buttons
