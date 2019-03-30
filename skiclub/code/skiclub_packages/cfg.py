# Sets config items


# Edit this dictionary to store service parameters

# IN PARTICULAR CHANGE :
# The backup_passphrase to a complex string, this is used as the key to encrypt database dumps
# The database_directory to a directory where the sqlite database will be kept, if left empty
# the .../projectfiles/project directory will be used

_CONFIG = {
            'redis_ip' : 'localhost',
            'redis_port' : 6379,
            'redis_auth' : '',
            'backup_passphrase' : "zdl556 && 0 tbbbUN",
            'database_directory' :''
          }


def get_redis():
    "Returns tuple of redis ip, port, auth"
    return (_CONFIG['redis_ip'], _CONFIG['redis_port'], _CONFIG['redis_auth'])

def get_backup_passphrase():
    "Returns the passphrase used to encrypt backup files"
    return _CONFIG['backup_passphrase']

def get_database_directory():
    "Returns the directory where the database is kept"
    return _CONFIG['database_directory']
