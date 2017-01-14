# This package contains code for populating pages which do not require user login to access
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



from ....skilift import FailPage

from . import home, login



def submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Depending on the submit list, call the appropriate package function"

    # submit_list[0] is the string 'public' and has already been used to call this fuction
    assert submit_list[0] == 'public'

    if submit_list[1] == 'home':
        try:
            submitfunc = getattr(home, submit_list[2])
        except:
            raise FailPage("submit_list contains 'public', 'home', but the required function is not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    if submit_list[1] == 'login':
        try:
            submitfunc = getattr(login, submit_list[2])
        except:
            raise FailPage("submit_list contains 'public', 'login', but the required function is not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


    raise FailPage("submit_list module string %s not recognised" % (submit_list[1],))
