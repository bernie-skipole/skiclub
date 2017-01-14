##################################
#
# These functions populate the top public pages
#
##################################



from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import sun



def create_index(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in home index page"

    # Called by responder id 1

    # fill table for two nights
    night0, night1 = sun.twoday_slots()
    page_data['slots', 'col0'] = [ str(slot) for slot in night0 ]
    page_data['slots', 'col1'] = [ str(slot) for slot in night1 ]

    page_data['slots', 'title1'] = "Tonight"
    page_data['slots', 'title2'] = "Tomorrow night"