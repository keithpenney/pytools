# Trying to spin up my own control script for controlling power of this "iBoot G2" network-enabled
# power switch

import requests

DEBUG=False
def _print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def session(url, state=False):
    print("Querying iBoot-G2 at {}".format(url))
    # First send generic GET to obtain session cookie
    auth = requests.auth.HTTPBasicAuth("admin", "admin")
    for n in range(2):
        _print("Initial GET")
        req = requests.get("http://{}".format(url), auth=auth)
        if req.ok:
            break
        else:
            _print("RESPONSE: ", req)
    _print("GET response headers:", req.headers)
    # Session cookie
    cookie = req.headers.get("Cookie", None)
    statestr = "ON" if state else "OFF"
    data = {
        "ck0": "ck0",
        "{}".format(statestr.lower()): "Power+{}".format(statestr.upper()),
    }
    _print(data)
    # Use the returned session cookie to POST your desired state change
    headers = {}
    if cookie is not None:
        headers["Cookie"] = cookie
    print("Attempting to set state {}".format(statestr))
    req = requests.post("http://{}/index.html".format(url), data=data, headers=headers, auth=auth)
    if req.ok:
        print("Success")
    else:
        print("Fail")
        print("RESPONSE: ", req)
        _print("POST response headers:")
        _print(req.headers)
    return

def doPowerSwitch():
    smap = {
        "off": 0,
        "0": 0,
        "on": 1,
        "1": 1,
    }
    import argparse
    parser = argparse.ArgumentParser("Set the state of iBoot-G2 network-enabled switch")
    parser.add_argument("state", choices=[key for key in smap.keys()], help="The desired state (on/off)")
    parser.add_argument("-a", "--addr", default="192.168.1.254", help="iBoot-G2 IP address")
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help="Verbose mode.")
    args = parser.parse_args()
    if args.verbose:
        global DEBUG
        DEBUG=True
    state = smap.get(args.state.lower().strip(), None)
    if state is None:
        print(parser.help)
        return
    session(args.addr, state=state)
    return

if __name__ == "__main__":
    doPowerSwitch()
