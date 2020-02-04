"""
Module for extracting data from HTTP HEAD/GET/POST responses using regular expressions.
"""

import re

CSRF_REGEX = r"csrftoken=(.*?);"
SESSION_ID_REGEX = r"sessionid=(.*?);"
RESPONSE_CODE_REGEX = r"HTTP/1\.1 (\d+).*"
PROFILE_HREF_REGEX = "href=\"/fakebook/(\\d+)/"
FRIEND_PAGE_REGEX = "friends/(\\d+)/\">"
SECRET_FLAG_REGEX = "FLAG: (.*?)</h2>"


def get_csrf_session_id(response):
    csrf_result = re.search(CSRF_REGEX, response)
    session_id_result = re.search(SESSION_ID_REGEX, response)
    return (csrf_result.group(1), session_id_result.group(1))


def get_session_id(response):
    session_id_result = re.search(SESSION_ID_REGEX, response)
    return session_id_result.group(1)


def get_status_code(response):
    response_code_result = re.search(RESPONSE_CODE_REGEX, response)
    if response_code_result:
        return response_code_result.group(1)
    return None


def get_profile_refs(response):
    ref_results = re.findall(PROFILE_HREF_REGEX, response)
    return ref_results


def print_secret_flag(response):
    # Assumption: max one secret flag per page
    flag = re.search(SECRET_FLAG_REGEX, response)
    if flag:
        print(flag.group(1))


def get_num_friend_pages(response):
    friend_pages_vals = re.findall(FRIEND_PAGE_REGEX, response)
    return len(friend_pages_vals)