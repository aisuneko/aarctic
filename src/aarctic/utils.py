import socket
import glob
from importlib_resources import files

def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))            # Bind to a free port provided by the host
        return s.getsockname()[1]  # Return the port number assigned


def get_dicts(location):
    return glob.glob(f'{location}/*.slob')


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
