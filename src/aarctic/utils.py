import socket
import glob
import json
import urllib.request
import urllib.error
from importlib_resources import files


def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))            # Bind to a free port provided by the host
        return s.getsockname()[1]  # Return the port number assigned


def get_dicts(location):
    return glob.glob(f'{location}/*.slob')


def server_parser(address, dict_dir):
    # 0 - OK, 1 - ERR, 2 - WARN
    has_dicts = bool(get_dicts(dict_dir))
    if not has_dicts:
        return (2, "No dictionaries found. Please set a valid folder in settings")
    try:
        response = urllib.request.urlopen(address)
        string = response.read().decode('utf-8')
        data = json.loads(string)
    except urllib.error.URLError:
        return (1, "Could not communicate with local server")
    except json.decoder.JSONDecodeError:
        return (1, "Error parsing data from local server")
    else:
        if has_dicts and not data:
            return (2, "No results returned")
        else:
            return (0, data)


def build_dicts_info(data):
    s = ""
    for idx, i in enumerate(data):
        s += f"<b>Dict #{idx+1}: {i['tags']['label']}</b><br><br>"
        for subitem in i:
            s += f"{subitem}: {i[subitem]}<br>"
        # TODO: prettify 'tags' json output
        s += "<br>"
    return s


def uifile(name):
    return files('aarctic.ui').joinpath(name)


debug = False
INTERFACE = '127.0.0.1'
