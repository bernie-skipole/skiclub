
#############################################
#
# These functions are used by an administrator to edit users
#
#############################################


from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops, send_email


def add_user(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in adduser index page"
    # Called from responder 3010
    page_data['newrole', 'option_list'] = ['Member', 'Admin', 'Guest']
    page_data['newrole', 'selectvalue'] = 'Member'
    if ('newuserresult','para_text') not in page_data:
        page_data['newuserresult','para_text'] = """Adding a user will generate a password, which will be emailed to the user if an email address is set and the 'Email password' checkbox is ticked."""


def submit_add_user(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Adds a user"
    # Called from responder 3011
    newuser = call_data['newuser', 'input_text']
    if not newuser:
        raise FailPage("The new username is missing.", displaywidgetname = 'newuserresult' )
    # check newuser does not currently exist in database
    if database_ops.get_user_id(newuser):
        # user id found for this user
        raise FailPage("This username already exits.", displaywidgetname = 'newuserresult' )
    if call_data['newrole','selectvalue'] == "Admin":
        # role initially set to member, changed to admin when a PIN is input
        newrole = 'MEMBER'
    elif call_data['newrole','selectvalue'] == "Member":
        newrole = 'MEMBER'
    else:
        newrole = "GUEST"
    newmember = call_data['newmember','input_text']
    if not newmember:
        newmember = "0000"
    newemail = call_data['newemail','input_text']
    if not newemail:
        newemail = None
    result = database_ops.adduser(newuser, newrole, newmember, newemail)
    if not result:
        raise FailPage("Unable to add new user", displaywidgetname = 'newuserresult')
    new_user_id, password = result
    # user added with new user id
    call_data['edited_user_id'] = new_user_id
    page_data['showresult','show'] = True
    page_data['pararesult','para_text'] = "User %s added with password %s" % (newuser, password)
    if (('sendemail','checkbox') in call_data) and (call_data['sendemail','checkbox'] == 'send'):
        if newemail:
            message = """You have been registered with %s,
with username %s and password %s
Please log on and change the password as soon as possible.""" % (call_data['org_name'], newuser, password)
            if send_email.sendmail(newemail,  "Automated message from %s" % (call_data['org_name'],), message):
                page_data['pararesult','para_text'] += "\nEmail with password sent to %s" % (newemail,)
            else:
                page_data['pararesult','para_text'] += "\nEmail not sent (failed to contact smtp server)."
        else:
            page_data['pararesult','para_text'] += "\nEmail not sent (no email address given)."
    if call_data['newrole','selectvalue'] == "Admin":
        # If Admin go to set pin page
        raise GoTo(target=3615, clear_submitted=True, clear_page_data=False)



def show_edit_users_page(page_data, offset=0, names=True):
    """Fills in editusers index page, populates table ordered by name or membership number
          Called by multiple functions in this module to re-fill the page after an edit operation"""

    #      The users,contents widgfield is a list of lists to fill the table
    #               col 0, 1 and 2 is the text to place in the first three columns,
    #               col 3, 4 is the two get field contents of the first link
    #               col 5, 6 is the two get field contents of the second link
    #               col 7 - True if the first button and link is to be shown, False if not
    #               col 8 - True if the second button and link is to be shown, False if not
    contents = []
    rows = 20
    getrows = rows+5

    # table can be ordered by name or membership number

    if names:
        page_data['order', 'button_text'] = 'membership number'
        page_data['order', 'link_ident'] = 'editmembers'
        page_data['next', 'link_ident'] = 'nextusers'
        page_data['previous', 'link_ident'] = 'nextusers'
        page_data['users', 'link_ident2'] = 'confirm_delete_user'
        page_data['users', 'json_ident2'] = 'json_confirm_delete_user'
    else:
        page_data['order', 'button_text'] = 'username'
        page_data['order', 'link_ident'] = 'editusers'
        page_data['next', 'link_ident'] = 'nextmembers'
        page_data['previous', 'link_ident'] = 'nextmembers'
        page_data['users', 'link_ident2'] = 'confirm_delete_member'
        page_data['users', 'json_ident2'] = 'json_confirm_delete_member'

    if not offset:
        u_list = database_ops.get_users(limit=getrows, names=names)
        if len(u_list) == getrows:
            u_list = u_list[:-5]
            page_data['next', 'get_field1'] = rows
        else:
            page_data['next', 'show'] = False
        for u in u_list:
            user_row = [u[1], u[2], u[3], u[0], '', u[0], '0', True, True]
            contents.append(user_row)
        page_data['users', 'contents'] = contents
        # no previous button
        page_data['previous', 'show'] = False
        return
    # so an offset is given
    u_list = database_ops.get_users(limit=getrows, offset=offset, names=names)
    if len(u_list) == getrows:
        u_list = u_list[:-5]
        page_data['next', 'get_field1'] = offset + rows
    else:
        page_data['next', 'show'] = False
    str_offset = str(offset)
    for u in u_list:
        user_row = [u[1], u[2], u[3], u[0], '', u[0], str_offset, True, True]
        contents.append(user_row)
    page_data['users', 'contents'] = contents
    # set previous button
    if offset == 0:
        page_data['previous', 'show'] = False
    elif offset < rows:
        page_data['previous', 'get_field1'] = 0
    else:
        page_data['previous', 'get_field1'] = offset - rows


def edit_users(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in editusers index page, populates table ordered by name"
    # Called by responder 3040
    show_edit_users_page(page_data, offset=0, names=True)


def edit_members(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in editusers index page, populates table ordered by membership number"
    # Called by responder 3050
    show_edit_users_page(page_data, offset=0, names=False)


def next_users(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in editusers index page, populates table ordered by username, gets next page of users"
    # Called by responder 3041
    if (('next', 'get_field1') in call_data) and call_data['next', 'get_field1']:
        try:
            offset = int(call_data['next', 'get_field1'])
        except:
            offset = 0
    elif (('previous', 'get_field1') in call_data) and call_data['previous', 'get_field1']:
        try:
            offset = int(call_data['previous', 'get_field1'])
        except:
            offset = 0
    else:
        offset = 0
    show_edit_users_page(page_data, offset=offset, names=True)


def next_members(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in editusers index page, populates table ordered by membership number, gets next page of members"
    # Called by responder 3051
    if (('next', 'get_field1') in call_data) and call_data['next', 'get_field1']:
        try:
            offset = int(call_data['next', 'get_field1'])
        except:
            offset = 0
    elif (('previous', 'get_field1') in call_data) and call_data['previous', 'get_field1']:
        try:
            offset = int(call_data['previous', 'get_field1'])
        except:
            offset = 0
    else:
        offset = 0
    show_edit_users_page(page_data, offset=offset, names=False)


def confirm_delete_user(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Populates and displays confirm box"
    # Called by responder 3060
    if ('users', 'get_field2_1') in call_data:
        user_id = int(call_data['users', 'get_field2_1'])
    else:
        raise FailPage("User ID not given.")
    user = database_ops.get_user_from_id(user_id)
    if user is None:
        raise FailPage("User ID not recognised.")
    if ('users', 'get_field2_2') in call_data:
        offset = int(call_data['users', 'get_field2_2'])
    else:
        offset=0
    show_edit_users_page(page_data, offset=offset, names=True)
    page_data['confirm', 'hide'] = False
    page_data['confirm', 'para_text'] = "Confirm delete user %s" % user[0]
    page_data['confirm','get_field1_1'] = 'username'
    page_data['confirm','get_field1_2'] = str(offset)
    page_data['confirm','get_field2_1'] = 'username'
    page_data['confirm','get_field2_2'] = str(offset)
    page_data['confirm','get_field2_3'] = str(user_id)


def confirm_delete_member(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Populates and displays confirm box"
    # Called by responder 3070
    if ('users', 'get_field2_1') in call_data:
        user_id = int(call_data['users', 'get_field2_1'])
    else:
        raise FailPage("User ID not given.")
    user = database_ops.get_user_from_id(user_id)
    if user is None:
        raise FailPage("User ID not recognised.")
    if ('users', 'get_field2_2') in call_data:
        try:
            offset = int(call_data['users', 'get_field2_2'])
        except:
            offset = 0
    else:
        offset = 0
    show_edit_users_page(page_data, offset=offset, names=False)
    page_data['confirm', 'hide'] = False
    page_data['confirm', 'para_text'] = "Confirm delete user %s" % user[0]
    page_data['confirm','get_field1_1'] = 'member'
    page_data['confirm','get_field1_2'] = str(offset)
    page_data['confirm','get_field2_1'] = 'member'
    page_data['confirm','get_field2_2'] = str(offset)
    page_data['confirm','get_field2_3'] = str(user_id)


def json_confirm_delete_user(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Populates and displays confirm box"
    # Called by responder 3065
    if ('users', 'get_field2_1') in call_data:
        user_id = int(call_data['users', 'get_field2_1'])
    else:
        raise FailPage("User ID not given.")
    user = database_ops.get_user_from_id(user_id)
    if user is None:
        raise FailPage("User ID not recognised.")
    if ('users', 'get_field2_2') in call_data:
        offset = int(call_data['users', 'get_field2_2'])
    else:
        offset=0
    page_data['confirm', 'hide'] = False
    page_data['confirm', 'para_text'] = "Confirm delete user %s" % user[0]
    page_data['confirm','get_field1_1'] = 'username'
    page_data['confirm','get_field1_2'] = str(offset)
    page_data['confirm','get_field2_1'] = 'username'
    page_data['confirm','get_field2_2'] = str(offset)
    page_data['confirm','get_field2_3'] = str(user_id)


def json_confirm_delete_member(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Populates and displays confirm box"
    # Called by responder 3075
    if ('users', 'get_field2_1') in call_data:
        user_id = int(call_data['users', 'get_field2_1'])
    else:
        raise FailPage("User ID not given.")
    user = database_ops.get_user_from_id(user_id)
    if user is None:
        raise FailPage("User ID not recognised.")
    if ('users', 'get_field2_2') in call_data:
        try:
            offset = int(call_data['users', 'get_field2_2'])
        except:
            offset = 0
    else:
        offset = 0
    page_data['confirm', 'hide'] = False
    page_data['confirm', 'para_text'] = "Confirm delete user %s" % user[0]
    page_data['confirm','get_field1_1'] = 'member'
    page_data['confirm','get_field1_2'] = str(offset)
    page_data['confirm','get_field2_1'] = 'member'
    page_data['confirm','get_field2_2'] = str(offset)
    page_data['confirm','get_field2_3'] = str(user_id)



def cancel_delete(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Cancels the confirm box"
    # Called by responder 3080
    if ('confirm','get_field1_1') in call_data:
        if call_data['confirm','get_field1_1'] == 'member':
            names=False
        else:
            names = True
    else:
        names=True
    if ('confirm','get_field1_2') in call_data:
        try:
            offset = int(call_data['confirm','get_field1_2'])
        except:
            offset=0
    else:
        offset=0
    show_edit_users_page(page_data, offset=offset, names=names)


def delete_user(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Deletes a user"
    # Called by responder 3090
    # get user id to delete
    if ('confirm','get_field2_3') in call_data:
        try:
            user_id = int(call_data['confirm','get_field2_3'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    try:
        admin_user_id = int(call_data['user_id'])
    except:
        raise FailPage("Invalid admin user")
    if admin_user_id == user_id:
        raise  FailPage("Invalid Operation: Cannot delete yourself")
    if user_id == 1:
        raise  FailPage("Cannot delete special Admin user")
    if not database_ops.delete_user_id(user_id):
        raise  FailPage("Database operation failed.")
    if ('confirm','get_field2_1') in call_data:
        if call_data['confirm','get_field2_1'] == 'member':
            names=False
        else:
            names = True
    else:
        names=True
    if ('confirm','get_field2_2') in call_data:
        try:
            offset = int(call_data['confirm','get_field2_2'])
        except:
            offset=0
    else:
        offset=0
    show_edit_users_page(page_data, offset=offset, names=names)


def edituser(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Sets edited_user_id for fill_edituser_template responder"
    # Called by responder 3110
    if ('users','get_field1_1') in call_data:
        try:
            edited_user_id = int(call_data['users','get_field1_1'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    call_data['edited_user_id'] = edited_user_id


def edit_username(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Changes username"
    # Called by responder 3120
    if ('username','hidden_field1') in call_data:
        try:
            edited_user_id = int(call_data['username','hidden_field1'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    call_data['edited_user_id'] = edited_user_id
    if edited_user_id == 1:
        raise FailPage("Cannot change name of special Admin user")
    new_username = call_data['username','input_text']
    if not new_username:
        page_data['username', 'set_input_errored'] = True
        raise FailPage(message="Invalid username")
    user = database_ops.get_user_from_id(edited_user_id)
    if user is None:
        raise FailPage(message="The user has not been recognised")
    # user is (username, role, email, member)
    if user[0] == new_username:
        raise FailPage(message="The username has not changed")
    existinguser = database_ops.get_user_from_username(new_username)
    if existinguser is not None:
        raise FailPage(message="The new username already exists")
    if not database_ops.set_username(edited_user_id, new_username):
        raise  FailPage("Database operation failed.")
    # username changed
    page_data['username', 'set_input_accepted'] = True
    page_data['showresult','show'] = True
    page_data['pararesult','para_text'] = "Username changed to %s" % (new_username,)



def edit_role(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Changes user role"
    # Called by responder 3140
    if ('role','hidden_field1') in call_data:
        try:
            edited_user_id = int(call_data['role','hidden_field1'])
        except:
            raise FailPage(message="The user to be edited has not been recognised")
    else:
        raise FailPage("The user to be edited has not been recognised")
    call_data['edited_user_id'] = edited_user_id
    if edited_user_id == 1:
        raise FailPage("Cannot change role of special Admin user")
    new_role = call_data['role','selectvalue']
    if new_role == 'Admin':
        new_role = 'ADMIN'
    elif new_role == 'Member':
        new_role = 'MEMBER'
    else:
        new_role = 'GUEST'
    user = database_ops.get_user_from_id(edited_user_id)
    if user is None:
        raise FailPage(message="The user has not been recognised")
    # user is (username, role, email, member)
    if user[1] == new_role:
        raise FailPage(message="The role has not changed")
    # If role is ADMIN, then go to set pin page
    if new_role == 'ADMIN':
        raise GoTo(target=3615, clear_submitted=True, clear_page_data=False)
    if not database_ops.set_role(edited_user_id, new_role):
        raise  FailPage("Database operation failed.")
    # role changed
    page_data['showresult','show'] = True
    page_data['pararesult','para_text'] = "Role changed to %s" % (new_role,)



def edit_member_number(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Sets membership number and edited_user_id for fill_edituser_template responder"
    # Called by responder 3125
    if ('member','hidden_field1') in call_data:
        try:
            edited_user_id = int(call_data['member','hidden_field1'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    call_data['edited_user_id'] = edited_user_id
    if edited_user_id == 1:
        raise FailPage("Cannot change membership number of special Admin user")
    new_member_number = call_data['member','input_text']
    user = database_ops.get_user_from_id(edited_user_id)
    if user is None:
        raise FailPage(message="The user has not been recognised")
    # user is (username, role, email, member)
    if user[3] == new_member_number:
        raise FailPage(message="The membership number has not changed")
    if not database_ops.set_membership_number(edited_user_id, new_member_number):
        raise  FailPage("Database operation failed.")
    # membership number changed
    page_data['member', 'set_input_accepted'] = True
    page_data['showresult','show'] = True
    page_data['pararesult','para_text'] = "Membership number changed to %s" % (new_member_number,)


def edit_email(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Sets email and edited_user_id for fill_edituser_template responder"
    # Called by responder 3130
    if ('email','hidden_field1') in call_data:
        try:
            edited_user_id = int(call_data['email','hidden_field1'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    call_data['edited_user_id'] = edited_user_id
    if edited_user_id == 1:
        raise FailPage("Cannot change email of special Admin user")
    new_email = call_data['email','input_text']
    user = database_ops.get_user_from_id(edited_user_id)
    if user is None:
        raise FailPage(message="The user has not been recognised")
    # user is (username, role, email, member)
    if user[2] == new_email:
        raise FailPage(message="The email address has not changed")
    if not database_ops.set_email(edited_user_id, new_email):
        raise  FailPage("Database operation failed.")
    # email changed
    page_data['email', 'set_input_accepted'] = True
    page_data['showresult','show'] = True
    if new_email:
        page_data['pararesult','para_text'] = "Email changed to %s" % (new_email,)
    else:
        page_data['pararesult','para_text'] = "No email set"


def make_password(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Generates and sets a password for edited user"
    # Called by responder 3135
    if ('newpassword','hidden_field1') in call_data:
        try:
            edited_user_id = int(call_data['newpassword','hidden_field1'])
        except:
            raise FailPage("User ID not recognised.")
    else:
        raise FailPage("User ID not recognised.")
    call_data['edited_user_id'] = edited_user_id
    if edited_user_id == 1:
        raise FailPage("Cannot change password of special Admin user")
    new_password = database_ops.new_password(edited_user_id)
    if not new_password:
        raise  FailPage("Database operation failed.")
    # password changed
    page_data['showresult','show'] = True
    page_data['pararesult','para_text'] = "New password created for this user, and set to %s" % (new_password,)
    user_email = database_ops.get_email(edited_user_id)
    if user_email and (('emailpassword','checkbox') in call_data) and (call_data['emailpassword','checkbox'] == 'emailpassword'):
        message = """A new password has been created for access to %s,
      Password:  %s
Please log on and change the password as soon as possible.""" % (call_data['org_name'], new_password)
        if send_email.sendmail(user_email,  "Automated message from %s" % (call_data['org_name'],), message):
            page_data['pararesult','para_text'] += "\nEmail with password sent to %s" % (user_email,)
        else:
            page_data['pararesult','para_text'] += "\nEmail not sent (failed to contact smtp server)."


def fill_edituser_template(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Populates the edituser template page"
    # Called by responder 3605
    edited_user_id = call_data['edited_user_id']
    str_edited_user_id = str(edited_user_id)
    user = database_ops.get_user_from_id(edited_user_id)
    # user is (username, role, email, member)
    if user is None:
        raise FailPage("User ID not recognised.")
    page_data['usertitle', 'para_text'] = "User %s" % (user[0],)
    # role
    page_data['role', 'option_list'] = ['Member', 'Admin', 'Guest']
    page_data['role', 'hidden_field1'] = str_edited_user_id
    if user[1] == "ADMIN":
        page_data['role', 'selectvalue'] = 'Admin'
        page_data['current_role', 'para_text'] = 'Current role: Admin'
    elif user[1] == "MEMBER":
        page_data['role', 'selectvalue'] = 'Member'
        page_data['current_role', 'para_text'] = 'Current role: Member'
    else:
        page_data['role', 'selectvalue'] = 'Guest'
        page_data['current_role', 'para_text'] = 'Current role: Guest'
    if edited_user_id == call_data['user_id']:
        page_data['role', 'disabled'] = True
    # username
    page_data['username', 'input_text'] = user[0]
    page_data['username', 'hidden_field1'] = str_edited_user_id
    # membership number
    if user[3]:
        page_data['member', 'input_text'] = user[3]
        page_data['current_member', 'para_text'] = 'Current membership number: %s' % (user[3],)
    else:
        page_data['member', 'input_text'] = ''
        page_data['current_member', 'para_text'] = 'Current membership number:'
    page_data['member', 'hidden_field1'] = str_edited_user_id
    # email
    if user[2]:
        page_data['email', 'input_text'] = user[2]
        page_data['current_email', 'para_text'] = 'Current email: %s' % (user[2],)
        page_data['emailpassword','checked'] = True
    else:
        page_data['email', 'input_text'] = ''
        page_data['current_email', 'para_text'] = 'Current email:'
        page_data['emailpassword','checked'] = False
    page_data['email', 'hidden_field1'] = str_edited_user_id
    # generate new password
    page_data['newpassword', 'hidden_field1'] = str_edited_user_id

