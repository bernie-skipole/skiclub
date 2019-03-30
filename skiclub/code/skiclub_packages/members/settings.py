##################################
#
# These functions alter member settings. The user
# must be logged in to call  them
#
##################################


from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops


def user_settings(skicall):
    """Populates the user settings page"""

    # Called from responder 8001 to insert the users email into the email widget

    user_id = skicall.call_data['user_id']
    email = database_ops.get_email(user_id)
    if email:
        skicall.page_data['email', 'input_text'] = email


def confirm_deregister(skicall):
    """Confirms the user wishes to de-register himself"""
    user_id = skicall.call_data['user_id']
    user = database_ops.get_user_from_id(user_id)
    if user is None:
        raise FailPage("User ID not recognised.")
    skicall.page_data['confirm', 'hide'] = False
    skicall.page_data['confirm', 'para_text'] = "Confirm delete user %s" % user[0]


def deregister_user(skicall):
    "deregister a user"

    # get user id to delete
    user_id = skicall.call_data['user_id']
    if user_id == 1:
        raise FailPage("Cannot delete special Admin user")

    if not database_ops.delete_user_id(user_id):
        raise FailPage("Database operation failed.")

    skicall.call_data["authenticated"] = False
    skicall.call_data["loggedin"] = False
    skicall.call_data["role"] = ""
    del skicall.call_data['user_id']


def new_password(skicall):
    """Given old password and two copies of a new one, set the password"""

    # Users can change their own password
    # This function is called from responder 8002 to set a new password

    user_id = skicall.call_data['user_id']

    oldpassword = skicall.call_data['oldpassword', 'input_text']
    newpassword1 = skicall.call_data['newpassword1', 'input_text']
    newpassword2 = skicall.call_data['newpassword2', 'input_text']

    if (not oldpassword) or (not newpassword1) or (not newpassword2):
        raise FailPage('Password missing', widget = 'passworderror')

    if newpassword1 != newpassword2:
        raise FailPage("New password fields do not match", widget = 'passworderror')

    if len(newpassword1) < 5:
        raise FailPage("New password too short - five or more characters please", widget = 'passworderror')

    if newpassword1 == oldpassword:
        raise FailPage("The new password should be different to the old one", widget = 'passworderror')

    if not database_ops.check_password_of_user_id(user_id, oldpassword):
        # old password invalid
        raise FailPage('Invalid current password', widget = 'passworderror')

    # All ok, set the new password into the database
    if not database_ops.set_password(user_id, newpassword1):
        # Something failed
        raise FailPage('Unable to update database', widget = 'passworderror')

    # password updated, show status message
    skicall.page_data['passwordstatus', 'para_text'] = "A new password has been set"
    skicall.page_data['passwordstatus', 'hide'] = False


def set_email(skicall):
    """Sets the user email in the database"""

    # Users can change their own email
    # This function is called from responder 8003 to set a new email

    user_id = skicall.call_data['user_id']
    if ('email', 'input_text') not in skicall.call_data:
        raise FailPage('email missing', widget = 'passworderror')
    email = skicall.call_data['email', 'input_text']
    if not email:
        email = ""

    if database_ops.set_email(user_id, email):
        skicall.page_data['email', 'input_text'] = email
    else:
        raise FailPage('Unable to set email into database', widget = 'passworderror')

    # email updated, show status message
    if email:
        skicall.page_data['emailstatus', 'para_text'] = "A new email address has been set"
    else:
        skicall.page_data['emailstatus', 'para_text'] = "The email address has been deleted"
    skicall.page_data['emailstatus', 'show'] = True
    skicall.page_data['email', 'set_input_accepted'] = True


