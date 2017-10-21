# Sets config items


# Edit this dictionary to store service parameters

_CONFIG = {
            'redis_ip' : 'localhost',
            'redis_port' : 6379,
            'redis_auth' : 'creampie'
          }


def get_redis():
    "Returns tuple of redis ip, port, auth"
    return (_CONFIG['redis_ip'], _CONFIG['redis_port'], _CONFIG['redis_auth'])
