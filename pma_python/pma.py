import os
from os.path import join
from urllib.parse import quote
from pma_python import version

import requests

__version__ = version.__version__

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


def _pma_http_get(url, headers, verify=True):
    global _pma_url_content
    global _pma_debug

    if not (url in _pma_url_content):
        if _pma_debug is True:
            print("Retrieving ", url)
        r = requests.get(url, headers=headers, verify=verify)
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


def get_supported_formats(pandas=False, verify=True):
    """
    Get an up-to-date list of all supported file formats on the Pathomation software platform
    """
    global _pma_debug
    url = "https://host.pathomation.com/etc/supported_formats.php"

    if _pma_debug == True:
        print(url)

    headers = {'Accept': 'application/json'}
    r = requests.get(url, headers=headers, verify=verify)
    json = r.json()

    if (pandas == True):
        import pandas as pd
        return pd.DataFrame.from_records(json, index=["vendor"])
    else:
        return json
