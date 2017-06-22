
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
        raise FailPage('Invalid settings.', widget = 'emailsettings')
    if starttls == 'checked':
        starttls = True
    else:
        starttls = False
    if database_ops.set_emailserver(emailuser, emailpassword, emailserver, no_reply, starttls):
        page_data['emailsettings', 'show_para'] = True
    else:
        raise FailPage('Unable to set smtp server settings into database', widget = 'emailsettings')



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


