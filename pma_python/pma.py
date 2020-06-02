from urllib.parse import quote
from os.path import join
import requests

__version__ = "2.0.0.121"

_pma_url_content = {}
_pma_debug = False


def _pma_join(*s):
    joinstring = ""
    for ss in s:
        if not (ss is None):
            joinstring = join(joinstring, ss)
    return joinstring.replace("\\", "/")


def _pma_q(arg):
    if (arg is None):
        return ''
    else:
        return quote(str(arg), safe='')


def _pma_http_get(url, headers):
    global _pma_url_content
    global _pma_debug

    if not (url in _pma_url_content):
        if _pma_debug is True:
            print("Retrieving ", url)
        r = requests.get(url, headers=headers)
        _pma_url_content[url] = r

    return _pma_url_content[url]


def _pma_clear_url_cache():
    global _pma_url_content
    _pma_url_content = {}


def _pma_set_debug_flag(flag):
    """
    Determine whether pma_python runs in debugging mode or not.
    When in debugging mode (flag = true), extra output is produced when certain conditions in the code are not met
    """
    global _pma_debug

    if not isinstance(flag, (bool)):
        raise Exception("flag argument must be of class bool")
    _pma_debug = flag
    if flag is True:
        print("Debug flag enabled. You will receive extra feedback and messages from pma_python (like this one)")
