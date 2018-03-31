########################################
#
# These functions backup and restore the database
#
########################################


import os, subprocess

from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops, cfg



def dumpdatabase(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Creates an encrypted database dump to file backup.bak"""
    # To decrypt the file
    # gpg2 --batch --passphrase "passphrase" -d backup.bak

    # get the database dump
    dump = database_ops.stringdump()
    if dump is None:
        raise FailPage("Unable to obtain backup from the database")
    # create backup file location under static so it can be served
    backupfile = os.path.join(call_data["projectfiles"], call_data["project"], "static", "backup.bak")

    # remove any existing backup file
    if os.path.exists(backupfile):
        os.unlink(backupfile)

    homedir = cfg.get_database_directory()
    if not homedir:
        homedir = os.path.join(call_data["projectfiles"], call_data["project"])

    # call gpg2 to encrypt the dump

    args = ["gpg2"]

    args.append("--batch")
    args.append("-c")
    args.append("--homedir")
    args.append(homedir)
    args.append("--passphrase")
    args.append(cfg.get_backup_passphrase())
    args.append("-o")
    args.append(backupfile)
    try:
        subprocess.run(args, input=dump.encode("utf-8"), timeout=2)
    except:
        raise FailPage("Unable to create backup file")



def upload(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Uploads a backup file and restores the membership database"

    # Called by responder 3030

    if (('upload','action') not in call_data) or (not call_data['upload','action']):
        raise FailPage("Invalid file.", widget = 'upload' )

    homedir = cfg.get_database_directory()
    if not homedir:
        homedir = os.path.join(call_data["projectfiles"], call_data["project"])

    uploaded_data = call_data['upload','action']
    args = ["gpg2"]
    args.append("--batch")
    args.append("-d")
    args.append("--homedir")
    args.append(homedir)
    args.append("--passphrase")
    args.append(cfg.get_backup_passphrase())
    try:
        sp = subprocess.run(args, input=uploaded_data, stdout=subprocess.PIPE, timeout=2)
        database_ops.restoredatabase(sp.stdout.decode('utf-8'))
    except:
        raise FailPage('Restore Failed.', widget = 'upload')
