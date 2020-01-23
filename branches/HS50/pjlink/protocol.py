def read_until(s, term):
    data = []
    c = s.recv(1).decode('utf-8') # c = f.read(1)
    while c != term:
        data.append(c)
        c = s.recv(1).decode('utf-8') # c = f.read(1)
    return ''.join(data)

def to_binary(body, param, sep=' '):
    assert body.isupper()

    assert len(body) == 4
    assert len(param) <= 128

    return '%1' + body + sep + param + '\r'

def parse_response(s, data=''):
    if len(data) < 7:
        data += s.recv(2 + 4 + 1 - len(data)).decode('utf-8') # data += f.read(2 + 4 + 1 - len(data))

    #print (data)
    header = data[0]
    assert header == '%'

    version = data[1]
    # only class 1 is currently defined
    assert version == '1'

    body = data[2:6]
    # commands are case-insensitive, but let's turn them upper case anyway
    # this will avoid the rest of our code from making this mistake
    # FIXME: AFAIR this takes the current locale into consideration, it shouldn't.
    body = body.upper()

    sep = data[6]
    assert sep == '='

    param = read_until(s, '\r')

    return (body, param)

ERRORS = {
    'ERR1': 'undefined command',
    'ERR2': 'out of parameter',
    'ERR3': 'unavailable time',
    'ERR4': 'projector failure',
}

def send_command(s, req_body, req_param):
    data = to_binary(req_body, req_param)
    #print (data)
    s.send (data.encode('utf-8')) # f.write(data)
    #f.flush()

    resp_body, resp_param = parse_response(s)
    #print (resp_body, resp_param)
    assert resp_body == req_body

    if resp_param in ERRORS:
        return False, ERRORS[resp_param]
    return True, resp_param

