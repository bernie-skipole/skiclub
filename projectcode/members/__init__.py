# This package contains code for populating pages which require logged in access
# but do not need to be admin authorised
#
# Date : 20170103
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk
#
#
#   Copyright 2017 Bernard Czenkusz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.



from ....skilift import FailPage, GoTo

from . import settings, set_cookies, authenticate



def submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "If the user is logged in, then depending on the submit list, call the appropriate package function"

    # submit_list[0] is the string 'members' and has already been used to call this fuction
    assert submit_list[0] == 'members'

    if not call_data['loggedin']:
        # If the user is not logged in, divert to the home page
        raise GoTo(target='home', clear_submitted=True, clear_page_data=True)

    if submit_list[1] == 'settings':
        try:
            submitfunc = getattr(settings, submit_list[2])
        except:
            raise FailPage("submit_list contains 'members', 'settings', but the required function is not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    if submit_list[1] == 'set_cookies':
        try:
            submitfunc = getattr(set_cookies, submit_list[2])
        except:
            raise FailPage("submit_list contains 'members', 'set_cookies', but the required function is not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    if submit_list[1] == 'authenticate':
        try:
            submitfunc = getattr(authenticate, submit_list[2])
        except:
            raise FailPage("submit_list contains 'members', 'authenticate', but the required function is not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


    raise FailPage("submit_list module string %s not recognised" % (submit_list[1],))

