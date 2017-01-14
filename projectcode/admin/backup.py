########################################
#
# These functions backup and restore the database
#
########################################



from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops



def dumpdatabase(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Returns a database dump, and sets the page header for an octet-stream"""

    # Called by responder 3022 which is of type SubmitIterator,
    # returns a list of sql script lines derived from a database dump

    # get a list of sql commands, and the content length from the database
    dump = database_ops.dumpdatabase()
    if dump is None:
        raise FailPage("Unable to obtain backup")
    sql_list, filelen = dump
    page_data['headers'] = [('content-type', 'application/octet-stream'), ('content-length', str(filelen))]
    return sql_list


def upload(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Uploads a backup file and restores the membership database"

    # Called by responder 3030

    if (('upload','action') not in call_data) or (not call_data['upload','action']):
        raise FailPage("Invalid file.", displaywidgetname = 'upload' )
    try:
        database_ops.restoredatabase(call_data['upload','action'].decode('utf-8'))
    except:
        raise FailPage('Restore Failed.', displaywidgetname = 'upload')
