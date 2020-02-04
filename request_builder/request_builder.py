"""
Module for building HTTP HEAD/GET/POST request strings.
"""

CRLF = "\r\n"


def generic_request_builder(method_name, path, headers, data={}):
    initial_request_line = method_name + " " + path + " HTTP/1.1" + CRLF
    data_string = ""
    for key, value in data.items():
        data_string = data_string + key + "=" + value + "&"
    data_string = data_string[0:-1]
    request_string = initial_request_line
    for (key, value) in headers.items():
        if key == 'Content-Length':
            value = str(len(data_string))
        request_string += key + ": " + value + CRLF
    return request_string + CRLF + data_string + CRLF + CRLF


def head_request(path, headers={}):
    return generic_request_builder("HEAD", path, headers)


def get_request(path, headers={}):
    return generic_request_builder("GET", path, headers)


def post_request(path, headers={}, data={}):
    return generic_request_builder("POST", path, headers, data)
