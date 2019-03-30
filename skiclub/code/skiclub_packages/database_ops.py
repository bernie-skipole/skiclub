"""
Module to create and query the members sqlite database

"""


import os, sqlite3, hashlib, random, shutil

from datetime import datetime, date, timedelta

from skipole import FailPage, GoTo, ValidateError, ServerError

from . import cfg

# These global values will be set when start_database is called
_DATABASE_PATH = ''
_DATABASE_EXISTS = False
_PROJECT = ''

# The following are set here, and could be changed if required
_DATABASE_DIR_NAME =  'members_database'
_DATABASE_NAME = 'members.db'

# This is the default admin username
_USERNAME = "admin"
# This is the default  admin password
_PASSWORD = "password"
# This is the default  admin PIN
_PIN = "1234"

# characters used in generated passwords - letters avoiding 0, O, 1, l, I, i, j, S, 5
_CHARS = "abcdefghkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXYZ2346789"
_CHARSPUNCT = _CHARS + "$%*+?"
# Default message
_MESSAGE = "New database created"
# The number of messages to retain
_N_MESSAGES = 10
# email server defaults
_MAIL_SERVER = 'smtp.googlemail.com'
_NO_REPLY = 'no_reply@xx.xx.xx'


def get_admin_user():
    return _USERNAME


def get_default_password():
    return _PASSWORD


def get_default_pin():
    return _PIN


def hash_password(user_id, password):
    "Return hashed password, on failure return None"
    global _PROJECT
    if not _PROJECT:
        return
    seed_password = _PROJECT + str(user_id) +  password
    hashed_password = hashlib.sha512( seed_password.encode('utf-8') ).digest()
    return hashed_password


def hash_pin(pin, seed):
    "Return hashed pin, on failure return None"
    seed_pin = seed + pin
    hashed_pin = hashlib.sha512( seed_pin.encode('utf-8') ).digest()
    return hashed_pin


def start_database(project, projectfiles):
    """Must be called first, before any other database operation to set globals"""
    global _DATABASE_PATH, _DATABASE_EXISTS, _PROJECT
    if _DATABASE_EXISTS:
        return
    # Set global variables
    _PROJECT = project
    database_dir = cfg.get_database_directory()
    if database_dir:
        database_dir = os.path.join(database_dir, _DATABASE_DIR_NAME)
    else:
        database_dir = os.path.join(projectfiles, project, _DATABASE_DIR_NAME)
    _DATABASE_PATH = os.path.join(database_dir, _DATABASE_NAME)
    _DATABASE_EXISTS = True
    # make the database directory
    if not os.path.isdir(database_dir):
        os.mkdir(database_dir)
    if os.path.isfile(_DATABASE_PATH):
        return
    # create the database
    con = open_database()
    try:
        # make table of users
        con.execute("create table users (USER_ID INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password BLOB, role TEXT, email TEXT, member TEXT)")
        # make table for admins, with pins
        con.execute("CREATE TABLE admins (user_id INTEGER PRIMARY KEY, pin1_2 BLOB, pin1_3 BLOB, pin1_4 BLOB, pin2_3 BLOB, pin2_4 BLOB, pin3_4 BLOB, FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)")
        # Make a table for server settings
        con.execute("CREATE TABLE serversettings (server_id TEXT PRIMARY KEY, emailuser TEXT, emailpassword TEXT, emailserver TEXT, no_reply TEXT, starttls INTEGER)")
        # create table of status message
        con.execute("CREATE TABLE messages (mess_id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, time TIMESTAMP, username TEXT)")
        # Create trigger to maintain only n messages
        n_messages = """CREATE TRIGGER n_messages_only AFTER INSERT ON messages
   BEGIN
     DELETE FROM messages WHERE mess_id <= (SELECT mess_id FROM messages ORDER BY mess_id DESC LIMIT 1 OFFSET %s);
   END;""" % (_N_MESSAGES,)
        con.execute(n_messages)
        # create database contents by inserting initial default values
        # make admin user password, role is 'ADMIN', user_id is 1
        hashed_password = hash_password(1, _PASSWORD)
        con.execute("insert into users (USER_ID, username, password, role, email, member) values (?, ?, ?, ?, ?, ?)", (None, _USERNAME, hashed_password,  'ADMIN', None, None))
        # set admin pin, with user_id 1
        set_pin(1, _PIN, con)
        # set email server settings
        con.execute("INSERT INTO serversettings (server_id,  emailuser, emailpassword, emailserver, no_reply, starttls) VALUES (?, ?, ?, ?, ?, ?)", ('1', None, None, _MAIL_SERVER, _NO_REPLY, 1))
        # set first message
        set_message( _USERNAME, _MESSAGE, con)
        con.commit()
    finally:
        con.close()


def database_directory():
    "Returns database directory"
    return os.path.dirname(_DATABASE_PATH)


def open_database():
    "Opens the database, and returns the database connection"
    if not _DATABASE_EXISTS:
        raise ServerError(message="Database does not exist.")
    if not _DATABASE_PATH:
       raise ServerError(message="Unknown database path.")
    # connect to database
    try:
        con = sqlite3.connect(_DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 1")
    except:
        raise ServerError(message="Failed database connection.")
    return con


def close_database(con):
    "Closes database connection"
    con.close()


def get_emailuserpass(con=None):
    "Return (emailusername, emailpassword) for server email account, return None on failure"
    if (not  _DATABASE_EXISTS):
        return
    if con is None:
        con = open_database()
        result = get_emailuserpass(con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select emailuser, emailpassword from serversettings where server_id = 1")
        result = cur.fetchone()
        if not result:
            return None
    return result


def get_emailserver(con=None):
    "Return (emailserver, no_reply, starttls) for server email account, return None on failure"
    if (not  _DATABASE_EXISTS):
        return
    if con is None:
        con = open_database()
        result = get_emailserver(con)
        con.close()
        return result
    cur = con.cursor()
    cur.execute("select emailserver, no_reply, starttls from serversettings where server_id = 1")
    result = cur.fetchone()
    if not result:
        return None
    if (not result[0]) or (not result[1]):
        return None
    return (result[0], result[1], bool(result[2]))


def set_emailserver(emailuser, emailpassword, emailserver, no_reply, starttls, con=None):
    "Return True on success, False on failure, this updates the email server settings, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not emailserver) or (not no_reply):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_emailserver(emailuser, emailpassword, emailserver, no_reply, starttls, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    try:
        con.execute("update serversettings set emailuser=?, emailpassword=?, emailserver = ?, no_reply=?,  starttls = ? where server_id = 1", (emailuser, emailpassword, emailserver, no_reply, int(starttls)))
    except:
        return False
    return True


def adduser(username, role="MEMBER", member="0000", email=None, con=None):
    "Return new user_id, password on success, None on failure, this generates a password and inserts a new user, if con given, does not commit"
    if (not  _DATABASE_EXISTS) or (not username) or (not role) or (not member):
        return False
    if con is None:
        try:
            con = open_database()
            result = adduser(username, role, member, email, con)
            if result is not None:
                con.commit()
            con.close()
        except:
            return
    else:
        try:
            # create a user, initially without a password
            con.execute("insert into users (USER_ID, username, password, role, email, member) values (?, ?, ?, ?, ?, ?)", (None, username, None,  role, email, member))
            cur = con.cursor()
            cur.execute("select user_id from users where username = ?", (username,))
            selectresult = cur.fetchone()
            if selectresult is None:
                return
            user_id = selectresult[0]
            # create six character password
            password = ''.join(random.choice(_CHARS) for x in range(6))
            hashed_password = hash_password(user_id, password)
            con.execute("update users set password = ? where user_id = ?", (hashed_password, user_id))
            result = user_id, password
        except:
            return
    return  result


def get_hashed_password_user_id(username, con=None):
    "Return (hashed_password, user_id) for username, return None on failure"
    if (not  _DATABASE_EXISTS) or (not username):
        return
    if con is None:
        con = open_database()
        result = get_hashed_password_user_id(username, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select password, user_id from users where username = ?", (username,))
        result = cur.fetchone()
        if not result:
            return
    return result


def get_hashed_password(user_id, con=None):
    "Return hashed_password for user_id, return None on failure"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    if con is None:
        con = open_database()
        result = get_hashed_password(user_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select password from users where user_id = ?", (user_id,))
        result = cur.fetchone()
        if not result:
            return
        result = result[0]
    return result


def set_password(user_id, password, con=None):
    "Return True on success, False on failure, this updates an existing user, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not user_id) or (not password):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_password(user_id, password, con)
            if result:
                con.commit()
            con.close()
        except:
            return False
        return result
    hashed_password = hash_password(user_id, password)
    try:
        con.execute("update users set password = ? where user_id = ?", (hashed_password, user_id))
    except:
        return False
    return True


def new_password(user_id, con=None):
    "Return password on success, None on failure, this generates a password for an existing user, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    if user_id == 1:
        return
    if con is None:
        try:
            con = open_database()
            password = new_password(user_id, con)
            if password:
                con.commit()
            con.close()
            return password
        except:
            return
    else:
        # create six character password
        password = ''.join(random.choice(_CHARS) for x in range(6))
        hashed_password = hash_password(user_id, password)
        try:
            con.execute("update users set password = ? where user_id = ?", (hashed_password, user_id))
        except:
            return
    return password


def check_password(username, password):
    "Returns True if this password belongs to this user, given a username"
    pwd_id = get_hashed_password_user_id(username)
    if not pwd_id:
        return False
    # Check if database hashed password is equal to the hash of the given password
    if pwd_id[0] == hash_password(pwd_id[1], password):
        # password valid
        return True
    return False


def check_password_of_user_id(user_id, password):
    "Returns True if this password belongs to this user, given a user_id"
    hashed_password = get_hashed_password(user_id)
    if not hashed_password:
        return False
    # Check if database hashed password is equal to the hash of the given password
    if hashed_password == hash_password(user_id, password):
        # password valid
        return True
    return False


def get_user_id(username, con=None):
    "Return user_id for user, return None on failure"
    if (not  _DATABASE_EXISTS) or (not username):
        return
    if con is None:
        con = open_database()
        user_id = get_user_id(username, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select user_id from users where username = ?", (username,))
        result = cur.fetchone()
        if result is None:
            return
        user_id = result[0]
    return user_id


def get_role(user_id, con=None):
    "Return role for user, return None on failure"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    if con is None:
        con = open_database()
        role = get_role(user_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select role from users where user_id = ?", (user_id,))
        result = cur.fetchone()
        if result is None:
            return
        role = result[0]
        if not role:
            return
    return role


def set_role(user_id, role, con=None):
    """Return True on success, False on failure, this updates the role of an existing user, if con given does not commit
          Trying to change role of user_id of 1 is a failure - cannot change role of special user Admin"""
    if (not  _DATABASE_EXISTS) or (not user_id):
        return False
    if user_id == 1:
        return False
    if role not in ('GUEST', 'MEMBER', 'ADMIN'):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_role(user_id, role, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        try:
            con.execute("update users set role = ? where user_id = ?", (role, user_id))
            if role != 'ADMIN':
                con.execute("delete from admins where user_id = ?", (user_id,))
        except:
            return False
    return True


def get_email(user_id, con=None):
    "Return email for user, return None on failure"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    if con is None:
        con = open_database()
        email = get_email(user_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select email from users where user_id = ?", (user_id,))
        result = cur.fetchone()
        if result is None:
            return
        email = result[0]
        if not email:
            return
    return email


def set_email(user_id, email, con=None):
    "Return True on success, False on failure, this updates the email of an existing user, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_email(user_id, email, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        try:
            con.execute("update users set email = ? where user_id = ?", (email, user_id))
        except:
            return False
    return True


def get_user_from_id(user_id, con=None):
    "Return (username, role, email, member) or None on failure"
    if not _DATABASE_EXISTS:
        return
    if con is None:
        con = open_database()
        user = get_user_from_id(user_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select username, role, email, member from users where user_id = ?", (user_id,))
        user = cur.fetchone()
        if not user:
            return
    return user


def get_user_from_username(username, con=None):
    "Return (user_id, role, email, member) or None on failure"
    if not _DATABASE_EXISTS:
        return
    if con is None:
        con = open_database()
        user = get_user_from_username(username, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select user_id, role, email, member from users where username = ?", (username,))
        user = cur.fetchone()
        if not user:
            return
    return user

def set_message(username, message, con=None):
    "Return True on success, False on failure, this inserts the message, if con given, does not commit"
    if (not  _DATABASE_EXISTS) or (not message) or (not username):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_message(username, message, con)
            if result:
                con.commit()
            con.close()
        except:
            return False
    else:
        try:
            con.execute("insert into messages (message, time, username) values (?,?,?)", (message, datetime.utcnow(), username))
        except:
            return False
    return  True


def get_all_messages(con=None):
    "Return string containing all messages return None on failure"
    if not  _DATABASE_EXISTS:
        return
    if con is None:
        con = open_database()
        m_string = get_all_messages(con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select message, time, username from messages order by mess_id DESC")
        m_string = ''
        for m in cur:
            m_string += m[1].strftime("%d %b %Y %H:%M:%S") + "\nFrom  " + m[2] + "\n" + m[0] + "\n\n"
    return m_string


def stringdump():
    "Returns a string being a dump of the sql database"
    if not  _DATABASE_EXISTS:
        return
    sql_list = []
    try:
        con = open_database()
        sql_list = list(con.iterdump())
    except:
        return
    finally:
        con.close()
    return "\n".join(sql_list)


def restoredatabase(sql_script):
    "Restore database"
    global _DATABASE_EXISTS
    # get special Admin user details
    try:
        con = open_database()
        cur = con.cursor()
        cur.execute("select username, password, role, email, member, user_id from users where user_id = 1")
        admin_user = cur.fetchone()
        cur.execute("select pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4, user_id from admins where user_id = 1")
        admin = cur.fetchone()
    except:
        return False
    finally:
        con.close()
    # remove directory contents
    database_dir = database_directory()
    shutil.rmtree(database_dir)
    # make directory
    os.mkdir(database_dir)
    try:
        con = sqlite3.connect(_DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 0")
        cur = con.cursor()
        cur.executescript(sql_script)
    except:
        shutil.rmtree(database_dir)
        _DATABASE_EXISTS = False
        return False
    finally:
        con.close()
    try:
        con = open_database()
        # Now re-insert Admin user
        con.execute("update users set username = ?, password = ?, role = ?, email = ?, member = ? where user_id = ?", admin_user)
        con.execute("update admins set pin1_2 = ?, pin1_3 = ?, pin1_4 = ?, pin2_3 = ?, pin2_4 = ?, pin3_4 = ? where user_id = ?", admin)
        con.commit()
    except:
        shutil.rmtree(database_dir)
        _DATABASE_EXISTS = False
        return False
    finally:
        con.close()
    return True


def get_users(limit=None, offset=None, names=True, con=None):
    "Return list of lists [user_id, username, role, membership number] apart from Admin user with user id 1"
    if not  _DATABASE_EXISTS:
        return
    if con is None:
        con = open_database()
        u_list = get_users(limit, offset, names, con)
        con.close()
    else:
        cur = con.cursor()
        if names:
            if limit is None:
                cur.execute("select user_id, username, role, member from users  where user_id != 1 order by username")
            elif offset is None:
                cur.execute("select user_id, username, role, member from users where user_id != 1 order by username limit ?", (limit,))
            else:
                cur.execute("select user_id, username, role, member from users where user_id != 1 order by username  limit ? offset ?", (limit, offset))
        else:
            if limit is None:
                cur.execute("select user_id, username, role, member from users where user_id != 1 order by cast (member as integer),username")
            elif offset is None:
                cur.execute("select user_id, username, role, member from users where user_id != 1 order by cast (member as integer), username limit ?", (limit,))
            else:
                cur.execute("select user_id, username, role, member from users where user_id != 1 order by cast (member as integer),username  limit ? offset ?", (limit, offset))
        u_list = []
        for u in cur:
            user_id = u[0]
            username = u[1]
            role = u[2]
            if u[3]:
                member = u[3]
            else:
                member = ''
            u_list.append([user_id, username, role, member])
    return u_list


def delete_user_id(user_id, con=None):
    """Delete user with given user_id. Return True on success, False on failure, if con given does not commit
       Trying to delete user_id of 1 is a failure - cannot delete special user Admin"""
    if (not  _DATABASE_EXISTS) or (not user_id):
        return False
    if user_id == 1:
        return False
    if con is None:
        try:
            con = open_database()
            result = delete_user_id(user_id, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        try:
            con.execute("delete from users where user_id = ?", (user_id,))
        except:
            return False
    return True


def set_username(user_id, new_username, con=None):
    """Return True on success, False on failure, this updates an existing user, if con given does not commit
          Trying to change name of user_id of 1 is a failure - cannot alter special user Admin"""
    if (not  _DATABASE_EXISTS) or (not user_id) or (not new_username):
        return False
    if user_id == 1:
        return False
    if con is None:
        try:
            con = open_database()
            result = set_username(user_id, new_username, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        try:
            con.execute("update users set username = ? where user_id = ?", (new_username, user_id))
        except:
            return False
    return True


def set_membership_number(user_id, new_member, con=None):
    "Return True on success, False on failure, this updates an existing user, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_membership_number(user_id, new_member, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        try:
            con.execute("update users set member = ? where user_id = ?", (new_member, user_id))
        except:
            return False
    return True


def set_pin(user_id, new_pin, con=None):
    "Return True on success, False on failure, this updates an existing admin, if con given does not commit"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return False
    if con is None:
        try:
            con = open_database()
            result = set_pin(user_id, new_pin, con)
            if result:
                con.commit()
            con.close()
            return result
        except:
            return False
    else:
        # The seed for each hash will consist of project + user_id + pair numbers
        part_seed = _PROJECT + str(user_id)
        pin1_2 = hash_pin(new_pin[0] + new_pin[1], seed=part_seed+'1')
        pin1_3 = hash_pin(new_pin[0] + new_pin[2], seed=part_seed+'2')
        pin1_4 = hash_pin(new_pin[0] + new_pin[3], seed=part_seed+'3')
        pin2_3 = hash_pin(new_pin[1] + new_pin[2], seed=part_seed+'4')
        pin2_4 = hash_pin(new_pin[1] + new_pin[3], seed=part_seed+'5')
        pin3_4 = hash_pin(new_pin[2] + new_pin[3], seed=part_seed+'6')
        try:
            con.execute("insert or replace into admins (user_id, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4) values (?, ?, ?, ?, ?, ?, ?)", (user_id, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4))
        except:
            return False
    return True

    
def get_admin(user_id, con=None):
    "Return admin row as a list on success, None on failure"
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    if con is None:
        con = open_database()
        result = get_admin(user_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select * from admins where user_id = ?", (user_id,))
        result = cur.fetchone()
        if not result:
            return
        # result is
        # user_id, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4
        # set result as list rather than tuple, so it can be changed
        result = list(result)
    return result


def make_admin(user_id, con=None):
    """Return PIN on success, None on failure, this creates a new admin, if the given user is not already an admin
          and generates a PIN for him.    If con given does not commit"""
    if (not  _DATABASE_EXISTS) or (not user_id):
        return
    # This function is not available for special user Admin
    if user_id == 1:
        return
    if con is None:
        try:
            con = open_database()
            result = make_admin(user_id, con)
            if result:
                con.commit()
            con.close()
        except:
            return
        return result
    # generate a pin
    new_pin = ''.join(random.choice(_CHARSPUNCT) for x in range(4))
    if not set_pin(user_id, new_pin, con):
        return
    if not set_role(user_id, 'ADMIN', con):
        return
    return new_pin


def get_administrators(con=None):
    """Get all admins (username, member, user_id) apart from special user Admin
           Returns None on failure or if none found"""
    if not  _DATABASE_EXISTS:
        return
    if con is None:
        try:
            con = open_database()
            result = get_administrators(con)
            con.close()
        except:
            return
        return result
    cur = con.cursor()
    cur.execute("select username, member, user_id from users where role = ? and user_id != 1 ORDER BY username ASC", ("ADMIN",))
    result = cur.fetchall()
    if not result:
        return
    return result


