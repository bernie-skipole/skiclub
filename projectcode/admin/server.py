
############################
#
# Sets server parameters
#
############################ 

from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops


def create_index(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in the setup index page"

    # called by responder 3001

    page_data['setup_buttons', 'nav_links'] = [['3010','Add User', True, ''],
                                                ['editusers','Edit Users', True, ''],
                                                ['home','Sessions', True, ''],
                                                ['3020','Server', True, '']]


def server_settings(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populates the server settings page"""

    # called by responder 3020

    ##### SMTP settings
    smtpserver = database_ops.get_emailserver()
    if not smtpserver:
        raise FailPage('Database access failure.')
    emailserver, no_reply, starttls = smtpserver
    if emailserver:
        page_data['emailserver', 'input_text'] = emailserver
    if no_reply:
        page_data['no_reply', 'input_text'] = no_reply
    if starttls:
        page_data['starttls', 'checked'] = True
    else:
        page_data['starttls', 'checked'] = False
    userpass = database_ops.get_emailuserpass()
    if not userpass:
        emailusername = ''
        emailpassword = ''
    else:
        emailusername, emailpassword = userpass
    if emailusername:
        page_data['emailuser', 'input_text'] = emailusername
    if emailpassword:
        page_data['emailpassword', 'input_text'] = emailpassword

    ##### Pi01 settings
    pi01server = database_ops.get_pi_config("01")
    if not pi01server:
        raise FailPage('Database access failure.')
    pi01_address, pi01_port, pi01_username, pi01_password = pi01server
    if pi01_address:
        page_data['pi01_address', 'input_text'] = pi01_address
    if pi01_port:
        page_data['pi01_port', 'input_text'] = pi01_port
    if pi01_username:
        page_data['pi01_username', 'input_text'] = pi01_username
    if pi01_password:
        page_data['pi01_password', 'input_text'] = pi01_password



def set_server_email_settings(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Sets the smtp settings in the database"""

    # called by responder 3021

    try:
        emailuser = call_data['emailuser', 'input_text']
        emailpassword = call_data['emailpassword', 'input_text']
        emailserver = call_data['emailserver', 'input_text']
        no_reply = call_data['no_reply', 'input_text']
        starttls = call_data['starttls', 'checkbox']
    except:
        raise FailPage('Invalid settings.', displaywidgetname = 'emailsettings')
    if starttls == 'checked':
        starttls = True
    else:
        starttls = False
    if database_ops.set_emailserver(emailuser, emailpassword, emailserver, no_reply, starttls):
        page_data['emailsettings', 'show_para'] = True
    else:
        raise FailPage('Unable to set smtp server settings into database', displaywidgetname = 'emailsettings')


def set_pi01_settings(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Sets the pi01 settings in the database"""

    # called by responder 3023

    try:
        pi01_address = call_data['pi01_address', 'input_text']
        pi01_port = call_data['pi01_port', 'input_text']
        pi01_username = call_data['pi01_username', 'input_text']
        pi01_password = call_data['pi01_password', 'input_text']
    except:
        raise FailPage('Invalid settings.', displaywidgetname = 'pi01settings')
    if database_ops.set_pi_config('01', pi01_address, pi01_port, pi01_username, pi01_password):
        page_data['pi01settings', 'show_para'] = True
    else:
        raise FailPage('Unable to set pi01 settings into database', displaywidgetname = 'pi01settings')


def add_message(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Adds a message"

    # called by responder 3002

    try:
        message = call_data['setstatus','input_text']
        username = call_data['username']
    except:
        raise FailPage('Invalid settings.')

    if database_ops.set_message(username, message):
        page_data['messageresult','para_text'] = "Message set."
    else:
        raise FailPage("Database access failure" )


