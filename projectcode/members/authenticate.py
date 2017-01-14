##################################
#
# These functions checks the administrative
# user's attempt to authenticate with a PIN, and
# if ok, sets the users status to authenticated
#
##################################


import random

from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops

# These functions require a list of the id numbers of the admin index pages
# which after authentication the call can be diverted to

_DIVERT = (3001, 8100, 9001)

# These being the page numbers of setup,  new pin, tests


def fill_input_pin(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills the page in which admin user sets a PIN which is to be tested"

    # called by responder 5515

    user_id  = call_data['user_id']

    # Check for locked out due to too many failed tries
    tries = database_ops.get_tries(user_id)
    if tries is None:
        raise FailPage(message="Invalid user")
    if tries > 2:
        raise FailPage(message= "Authentication locked out.")

    # Generate a random number, and set it into the database
    # and also as an hidden field in the form, so it is submitted when the user submits
    # a PIN and will be checked against the database.
    rnd = random.randint(1, 10000)
    if not database_ops.set_rnd(user_id, rnd):
        raise FailPage(message="Failure accessing the database")
    page_data['input_pin', 'hidden_field1'] = str(rnd)

    # As the call to this page is diverted from calling an admin function
    # we need the original page to call again after authentication,
    # so store this original requested page as a further hidden_field
    if call_data['called_ident'][0] == call_data['project']:
        # Only allow diversion to specific pages
        diverted_page = call_data['called_ident'][1]
        if diverted_page in _DIVERT:
            page_data['input_pin', 'hidden_field2'] = str(diverted_page )

    # Get the pair of pin characters to be requested
    pair = database_ops.get_pair(user_id)
    if not pair:
        raise FailPage(message="Failure accessing database")

    if pair == 1:
        page_data['input_text','para_text'] = "Please input the first and second characters of your PIN:"
        page_data['input_pin', 'pin1'] = True
        page_data['input_pin', 'pin2'] = True
        page_data['input_pin', 'pin3'] = False
        page_data['input_pin', 'pin4'] = False
    elif pair == 2:
        page_data['input_text','para_text'] = "Please input the first and third characters of your PIN:"
        page_data['input_pin', 'pin1'] = True
        page_data['input_pin', 'pin2'] = False
        page_data['input_pin', 'pin3'] = True
        page_data['input_pin', 'pin4'] = False
    elif pair == 3:
        page_data['input_text','para_text'] = "Please input the first and fourth characters of your PIN:"
        page_data['input_pin', 'pin1'] = True
        page_data['input_pin', 'pin2'] = False
        page_data['input_pin', 'pin3'] = False
        page_data['input_pin', 'pin4'] = True
    elif pair == 4:
        page_data['input_text','para_text'] = "Please input the second and third characters of your PIN:"
        page_data['input_pin', 'pin1'] = False
        page_data['input_pin', 'pin2'] = True
        page_data['input_pin', 'pin3'] = True
        page_data['input_pin', 'pin4'] = False
    elif pair == 5:
        page_data['input_text','para_text'] = "Please input the second and fourth characters of your PIN:"
        page_data['input_pin', 'pin1'] = False
        page_data['input_pin', 'pin2'] = True
        page_data['input_pin', 'pin3'] = False
        page_data['input_pin', 'pin4'] = True
    elif pair == 6:
        page_data['input_text','para_text'] = "Please input the third and fourth characters of your PIN:"
        page_data['input_pin', 'pin1'] = False
        page_data['input_pin', 'pin2'] = False
        page_data['input_pin', 'pin3'] = True
        page_data['input_pin', 'pin4'] = True
    else:
        raise FailPage(message="Failure accessing database")


def check_pin(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Checks submitted PIN"

    # called by responder 5021

    user_id  = call_data['user_id']
    diverted_page = None

    # ensure starting off with authention False
    if not database_ops.set_authenticated(user_id, False):
        # failed to set authenticated to False
        raise FailPage(message= "Unable to access database")
    call_data['authenticated'] = False

    admin = database_ops.get_admin(user_id)
    if not admin:
        raise FailPage(message="Invalid user")
    # admin is a list of 
    # user_id, authenticated, rnd, pair, tries, timestamp, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4

    # Test the number of tries
    if admin[4] > 2:
        raise FailPage(message= "Authentication locked out. Please try again after two hours.")
    try:
        # Increment tries
        if not database_ops.set_tries(user_id, admin[4] +1):
            raise FailPage(message= "Unable to access database")
        # Test rnd received is the same as the value in the database
        if admin[2] != int(call_data['input_pin','hidden_field1']):
            raise FailPage(message= "Invalid input")
        # If diverted page is present, check it is valid
        if (('input_pin', 'hidden_field2') in call_data) and call_data[('input_pin', 'hidden_field2')] :
            try:
                diverted_page = int(call_data[('input_pin', 'hidden_field2')])
            except:
                raise FailPage(message= "Invalid input")
            # Allowed values of pages to go to
            if diverted_page not in _DIVERT:
                raise FailPage(message= "Invalid input")
        # get pair of pin characters to be tested
        pair = admin[3]
        seed = call_data['project'] + str(user_id) + str(pair)
        if pair == 1:
            if call_data['input_pin', 'pin3'] or call_data['input_pin', 'pin4']:
                raise FailPage(message= "Invalid PIN")
            pin1_2 = database_ops.hash_pin(call_data['input_pin', 'pin1'] + call_data['input_pin', 'pin2'], seed)
            if pin1_2 != admin[6]:
                raise FailPage(message= "Invalid PIN")
        elif pair == 2:
            if call_data['input_pin', 'pin2'] or call_data['input_pin', 'pin4']:
                raise FailPage(message= "Invalid PIN")
            pin1_3 = database_ops.hash_pin(call_data['input_pin', 'pin1'] + call_data['input_pin', 'pin3'], seed)
            if pin1_3 != admin[7]:
                raise FailPage(message= "Invalid PIN")
        elif pair == 3:
            if call_data['input_pin', 'pin2'] or call_data['input_pin', 'pin3']:
                raise FailPage(message= "Invalid PIN")
            pin1_4 = database_ops.hash_pin(call_data['input_pin', 'pin1'] + call_data['input_pin', 'pin4'], seed)
            if pin1_4 != admin[8]:
                raise FailPage(message= "Invalid PIN")
        elif pair == 4:
            if call_data['input_pin', 'pin1'] or call_data['input_pin', 'pin4']:
                raise FailPage(message= "Invalid PIN")
            pin2_3 = database_ops.hash_pin(call_data['input_pin', 'pin2'] + call_data['input_pin', 'pin3'], seed)
            if pin2_3 != admin[9]:
                raise FailPage(message= "Invalid PIN")
        elif pair == 5:
            if call_data['input_pin', 'pin1'] or call_data['input_pin', 'pin3']:
                raise FailPage(message= "Invalid PIN")
            pin2_4 = database_ops.hash_pin(call_data['input_pin', 'pin2'] + call_data['input_pin', 'pin4'], seed)
            if pin2_4 != admin[10]:
                raise FailPage(message= "Invalid PIN")
        elif pair == 6:
            if call_data['input_pin', 'pin1'] or call_data['input_pin', 'pin2']:
                raise FailPage(message= "Invalid PIN")
            pin3_4 = database_ops.hash_pin(call_data['input_pin', 'pin3'] + call_data['input_pin', 'pin4'], seed)
            if pin3_4 != admin[11]:
                raise FailPage(message= "Invalid PIN")
        else:
            raise FailPage(message= "Authentication Failed")
        # user is authenticated
        if not database_ops.set_authenticated(user_id, True):
            # failed to set authenticated to True
            raise FailPage(message= "Unable to set Authenticate")
        call_data['authenticated'] = True
    except FailPage:
        raise
    except:
        raise FailPage(message= "Invalid input")
    if diverted_page:
        raise GoTo(target=diverted_page, clear_submitted=True, clear_page_data=True)
        
