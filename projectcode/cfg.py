# Sets config items


# Edit this dictionary to store service parameters

# IN PARTICULAR - Change the backup_passphrase

_CONFIG = {
            'redis_ip' : 'localhost',
            'redis_port' : 6379,
            'redis_auth' : '',
            'backup_passphrase' : "zdl556 && 0 tbbbUN"
          }


def get_redis():
    "Returns tuple of redis ip, port, auth"
    return (_CONFIG['redis_ip'], _CONFIG['redis_port'], _CONFIG['redis_auth'])

def get_backup_passphrase():
    "Returns the passphrase used to encrypt backup files"
    return _CONFIG['backup_passphrase']
