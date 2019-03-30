
import os, sys


skipole_package_location = "/home/bernie/mercurial/skipole"
if skipole_package_location not in sys.path:
    sys.path.append(skipole_package_location)



from skipole import WSGIApplication, FailPage, GoTo, ValidateError, ServerError, set_debug, use_submit_list


from skiclub_packages import database_ops, redis_ops


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


# the framework needs to know the location of the projectfiles directory holding this and
# other projects - specifically the skis and skiadmin projects
# The following line assumes, as default, that this file is located beneath
# ...projectfiles/skiclub/code/

PROJECTFILES = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PROJECT = 'skiclub'


# checks members database exists, if not create it
database_ops.start_database(PROJECT, PROJECTFILES)
# create a redis connection for miscellaneous use
rconn_0 = redis_ops.open_redis(redis_db=0)
# create a redis connection for logged in users
rconn_1 = redis_ops.open_redis(redis_db=1)
# and another for authenticated admins
rconn_2 = redis_ops.open_redis(redis_db=2)
# and another for user_id
rconn_3 = redis_ops.open_redis(redis_db=3)
# Set the organisation name into proj_data, used in page header and automated email
proj_data = {"org_name":"Example club membership project", 'rconn_0':rconn_0, 'rconn_1':rconn_1, 'rconn_2':rconn_2, 'rconn_3':rconn_3, 'projectfiles':projectfiles}



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

##############################################################################
#
# The above functions will be inserted into the skipole.WSGIApplication object
# and will be called as required
#
##############################################################################


# create the wsgi application
application = WSGIApplication(project=PROJECT,
                              projectfiles=PROJECTFILES,
                              proj_data=proj_data,
                              start_call=start_call,
                              submit_data=submit_data,
                              end_call=end_call,
                              url="/")

# This creates a WSGI application object. On being created the object uses the projectfiles location to find
# and load json files which define the project, and also uses the functions :
#     start_call, submit_data, end_call
# to populate returned pages.
# proj_data is an optional dictionary which you may use for your own purposes,
# it is included as the skicall.proj_data attribute


# The skis application must always be added, without skis you're going nowhere!
# The skis sub project serves javascript files required by the framework widgets.

skis_code = os.path.join(PROJECTFILES, 'skis', 'code')
if skis_code not in sys.path:
    sys.path.append(skis_code)
import skis
skis_application = skis.makeapp(PROJECTFILES)
application.add_project(skis_application, url='/lib')

# The add_project method of application, enables the added sub application
# to be served at a URL which should extend the URL of the main 'root' application.
# The above shows the main newproj application served at "/" and the skis library
# project served at "/lib"


# to deploy on a web server, you would typically install skipole on the web server,
# together with a 'projectfiles' directory containing the projects you want
# to serve (typically this project, and the skis project).
# you would then follow the web servers own documentation which should describe how
# to load a wsgi application.

# You could remove everything below here when deploying and serving
# the application. The following lines are used to serve the project locally
# and add the skiadmin project for development.

if __name__ == "__main__":

    # If called as a script, this portion runs the python wsgiref.simple_server
    # and serves the project. Typically you would do this with the 'skiadmin'
    # sub project added which can be used to develop pages for your project

    ############################### THESE LINES ADD SKIADMIN ######################
                                                                                  #
    set_debug(True)                                                               #
    skiadmin_code = os.path.join(PROJECTFILES, 'skiadmin', 'code')                #
    if skiadmin_code not in sys.path:                                             #
        sys.path.append(skiadmin_code)                                            #
    import skiadmin                                                               #
    skiadmin_application = skiadmin.makeapp(PROJECTFILES, editedprojname=PROJECT) #
    application.add_project(skiadmin_application, url='/skiadmin')                #
                                                                                  #
    ###############################################################################

    from wsgiref.simple_server import make_server

    # serve the application
    host = "127.0.0.1"
    port = 8000

    httpd = make_server(host, port, application)
    print("Serving %s on port %s. Call http://localhost:%s/skiadmin to edit." % (PROJECT, port, port))
    httpd.serve_forever()

