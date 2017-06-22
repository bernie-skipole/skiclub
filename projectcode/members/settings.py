##################################
#
# These functions alter member settings. The user
# must be logged in to call  them
#
##################################


from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops


def user_settings(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populates the user settings page"""

    # Called from responder 8001 to insert the users email into the email widget

    user_id = call_data['user_id']
    email = database_ops.get_email(user_id)
    if email:
        page_data['email', 'input_text'] = email


def new_password(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Given old password and two copies of a new one, set the password"""

    # Users can change their own password
    # This function is called from responder 8002 to set a new password

    user_id = call_data['user_id']

    oldpassword = call_data['oldpassword', 'input_text']
    newpassword1 = call_data['newpassword1', 'input_text']
    newpassword2 = call_data['newpassword2', 'input_text']

    if (not oldpassword) or (not newpassword1) or (not newpassword2):
        raise FailPage('Password missing', widget = 'passwordstatus')

    if newpassword1 != newpassword2:
        raise FailPage("New password fields do not match", widget = 'passwordstatus')

    if len(newpassword1) < 5:
        raise FailPage("New password too short - five or more characters please", widget = 'passwordstatus')

    if newpassword1 == oldpassword:
        raise FailPage("The new password should be different to the old one", widget = 'passwordstatus')

    if not database_ops.check_password_of_user_id(user_id, oldpassword):
        # old password invalid
        raise FailPage('Invalid current password', widget = 'passwordstatus')

    # All ok, set the new password into the database
    if not database_ops.set_password(user_id, newpassword1):
        # Something failed
        raise FailPage('Unable to update database', widget = 'passwordstatus')

    # password updated, show status message
    page_data['passwordstatus', 'show_para'] = True



def set_email(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Sets the user email in the database"""

    # Users can change their own email
    # This function is called from responder 8003 to set a new email

    user_id = call_data['user_id']
    if ('email', 'input_text') not in call_data:
        raise FailPage('email missing', widget = 'emailstatus')
    email = call_data['email', 'input_text']
    if not email:
        email = ""

    if database_ops.set_email(user_id, email):
        page_data['email', 'input_text'] = email
    else:
        raise FailPage('Unable to set email into database', widget = 'emailstatus')

    # email updated, show status message
    page_data['emailstatus', 'show_para'] = True
    page_data['email', 'set_input_accepted'] = True

