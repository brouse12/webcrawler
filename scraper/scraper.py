"""
Module for webscraping 'Fakebook' and printing located secret keys to the terminal. Call scraper.flow to login
with a username and password, and traverse 'Fakebook' via BFS.
"""

import socket
from request_builder import request_builder
from response_handler import response_handler
from collections import deque

HOST = "cs5700f16.ccs.neu.edu"
LOGIN_HEAD_PATH = "/accounts/login/?next=/fakebook/"
LOGIN_PATH = "/accounts/login/"
HOME_PATH = "/fakebook/"
BUFFER_SIZE = 4096


def headers_after_login(csrf, session_id):
    headers = {}
    headers['Connection'] = 'keep-alive'
    headers['Cookie'] = 'csrftoken=' + csrf + '; sessionid=' + session_id
    headers['Referer'] = 'http://cs5700f16.ccs.neu.edu/'
    return headers


def post_headers_for_login(crsf, session_id):
    headers = {}
    headers['Content-Length'] = ''
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    headers['Connection'] = 'keep-alive'
    headers['Cookie'] = 'csrftoken=' + crsf + '; session_id=' + session_id
    headers['Origin'] = 'http://cs5700f16.ccs.neu.edu'
    headers['Referer'] = 'http://cs5700f16.ccs.neu.edu/accounts/login/?next=/fakebook/'
    headers['Upgrade-Insecure-Requests'] = '1'
    return headers


def generic_request_headers():
    headers = {}
    headers['Host'] = HOST
    headers['User-Agent'] = "Python App"
    headers['Accept'] = "text/html,application/xhtml+xml,application/xml"
    headers['Cache-Control'] = "no-cache"
    headers['Connection'] = 'keep-alive'
    return headers


def open_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = (HOST, 80)
    s.connect(addr)
    return s


def send_request(s, request):
    status = "500"
    while status == "500":
        try:
            s.socket.send(request.encode())
            data = []
            resp = s.socket.recv(BUFFER_SIZE).decode()
            status = response_handler.get_status_code(resp)
            data.append(resp)
            retry = 5
            while not status and retry > 0:
                resp = s.socket.recv(BUFFER_SIZE).decode()
                data.append(resp)
                status = response_handler.get_status_code(resp)
                retry -= 1
        except TimeoutError:
            return retry_send(s, request)
    if not status:
        return retry_send(s, request)
    if status == "403" or status == "404":
        return None
    return "".join(data)


def retry_send(s, request):
    s.socket.close()
    s.socket = open_connection()
    return send_request(s, request)


def format_path(path_ext):
    return HOME_PATH + path_ext + "/"


def get_csrf_and_session_id_token(sock):
    head_request = request_builder.head_request(
        LOGIN_HEAD_PATH, generic_request_headers())
    response = send_request(sock, head_request)
    return response_handler.get_csrf_session_id(response)


def do_login(sock, username, password, csrf, session_id):
    post_data = {'csrfmiddlewaretoken': csrf, 'next': HOME_PATH,
                 'username': username, 'password': password}
    combined_headers = {**post_headers_for_login(csrf, session_id),
                        **generic_request_headers()}
    post_request = request_builder.post_request(
        LOGIN_PATH, combined_headers, post_data)
    return send_request(sock, post_request)


def get_page(sock, csrf, session_id, path):
    combined_headers = {**headers_after_login(csrf, session_id),
                        **generic_request_headers()}
    get_request = request_builder.get_request(path, combined_headers)
    response = send_request(sock, get_request)
    return response


def extract_friends_from_page(sock, csrf, session_id, page_path):
    friend_page = get_page(sock, csrf, session_id, page_path)
    if not friend_page:
        return None
    response_handler.print_secret_flag(friend_page)
    friends = response_handler.get_profile_refs(friend_page)
    return friends, friend_page


def flow(username, password):
    sock = open_connection()
    socket_wrapper = SocketWrapper(sock)
    csrf, session_id = get_csrf_and_session_id_token(socket_wrapper)
    post_login_response = do_login(socket_wrapper, username, password, csrf, session_id)
    session_id = response_handler.get_session_id(post_login_response)
    home_page = get_page(socket_wrapper, csrf, session_id, HOME_PATH)
    profile_refs = response_handler.get_profile_refs(home_page)
    bfs(socket_wrapper, csrf, session_id, profile_refs)


def bfs(sock, csrf, session_id, profiles):
    visited = {}
    q = deque(profiles)
    while q:
        # pop a profile page from the queue and search it for secret flags
        profile = q.popleft()
        if profile in visited:
            continue
        visited[profile] = True
        profile_path = format_path(profile)
        profile_page = get_page(sock, csrf, session_id, profile_path)
        if profile_page:
            response_handler.print_secret_flag(profile_page)
        # visit the profile's friend page, adding friends to queue and printing secret flags
        friend_page_path = profile_path + "friends/1/"
        friends, friend_page = extract_friends_from_page(sock, csrf, session_id, friend_page_path)
        if not friends:
            continue
        for f in friends:
            q.append(f)

        # if additional pages in friend list, visit them too
        num_friend_pages = response_handler.get_num_friend_pages(friend_page)
        for i in range(2, num_friend_pages):
            friend_page_path = profile_path + "friends/{}/".format(i)
            friends, friend_page = extract_friends_from_page(sock, csrf, session_id, friend_page_path)
            if not friends:
                continue
            for f in friends:
                q.append(f)


# Implement mutable socket for reconnecting. Could also be a global socket.
class SocketWrapper:
    def __init__(self, socket):
        self.socket = socket
