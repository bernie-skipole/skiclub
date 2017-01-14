########################################
#
# These functions edit PINS
#
########################################



from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops


def fill_new_pin(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populates the New PIN page, this is the page shown when an administrator chooses
          New PIN from the left navigation buttons"""

    # called from responder 8100

    result = database_ops.get_administrators()

    # Fills the table of administrators, the database call returns a list of lists in the
    # format required by the widget
     # Each inner list being (username, member, user_id) apart from special user Admin
    # col 0 and 1 are the text strings to place in the first two columns of the admins table
    # col 2 is the get field contents of the button link

    if not result:
        page_data['tabletext', 'show'] = False
        page_data['admins', 'show'] = False
    else:
        page_data['admins', 'contents'] = result



def set_your_pin(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Given the four characters of a pin, for the current logged in user sets it"""

    # called from responder 8101

    username = call_data['username']
    user_id = call_data['user_id']

    pin1 = call_data['newpin','pin1']
    if not pin1 or (len(pin1) != 1):
        raise FailPage('Invalid PIN', displaywidgetname = 'newpin')
    pin2 = call_data['newpin','pin2']
    if not pin2 or (len(pin2) != 1):
        raise FailPage('Invalid PIN', displaywidgetname = 'newpin')
    pin3 = call_data['newpin','pin3']
    if not pin3 or (len(pin3) != 1):
        raise FailPage('Invalid PIN', displaywidgetname = 'newpin')
    pin4 = call_data['newpin','pin4']
    if not pin4 or (len(pin4) != 1):
        raise FailPage('Invalid PIN', displaywidgetname = 'newpin')
    if database_ops.set_pin(user_id, [pin1, pin2, pin3, pin4], True):
        space_pin = pin1+' '+pin2+' '+pin3+' '+pin4
        page_data['showadminpin', 'para_text'] = "New PIN for user %s is %s" % (username, space_pin)
    else:
        raise FailPage('Unable to set new PIN into database', displaywidgetname = 'newpin')



def fill_generate_pin_template(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Fills the template page to generate a PIN for an edited user, this page is called when a user role
          is changed to Admin"""

    # called by responder 3615

    if not 'edited_user_id' in call_data:
        raise FailPage('Invalid user')
    edited_user_id = call_data['edited_user_id']

    if edited_user_id == 1:
        raise FailPage('This function is not available for this user.')

    edited_user = database_ops.get_user_from_id(edited_user_id)
    # edited user should be (username, role, email, member)
    if not edited_user:
        raise FailPage('Invalid user')

    page_data['pagetop','para_text'] = "Set Administrative access PIN for %s" % (edited_user[0],)
    page_data['newadminpin','get_field1'] = str(edited_user_id)



def make_pin(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Create a PIN for an edited user and set user to Admin role"""


    # called by responders 3160 and 3170

    try:
        edited_user_id = int(call_data['newadminpin'])
    except:
        raise FailPage('Invalid edited user')

    if edited_user_id == 1:
        raise FailPage('Cannot create random PIN for Admin')

    edited_user = database_ops.get_user_from_id(edited_user_id)
    # edited user should be (username, role, email, member)
    if not edited_user:
        raise FailPage('Invalid user')

    call_data['edited_user_id'] = edited_user_id
    # generate new pin
    new_pin = database_ops.make_admin(edited_user_id)
    if new_pin:
        space_pin = ' '.join( c for c in new_pin)
        page_data['showadminpin', 'para_text'] = 'New PIN for user %s is %s' % (edited_user[0], space_pin)
    else:
        raise FailPage('Failed database access, unable to set PIN')



