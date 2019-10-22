import os
from urllib.parse import quote
from urllib.request import urlopen
from pma_python import pma

import requests

__version__ = pma.__version__


def set_debug_flag(flag):
    """
    Determine whether pma_python runs in debugging mode or not.
    When in debugging mode (flag = true), extra output is produced when certain conditions in the code are not met
    """
    pma._pma_set_debug_flag(flag)


def get_version_info(pmaviewURL):
    """
    Get version info from PMA.view instance running at pmaviewURL
    """
    # purposefully DON'T use helper function _pma_api_url() here:
    # why? because GetVersionInfo can be invoked WITHOUT a valid SessionID;
    # _pma_api_url() takes session information into account
    url = pma._pma_join(pmaviewURL, "api/json/GetVersionInfo")
    version = ""
    try:
        # Are we looking at PMA.view/studio 2.x?
        if pma._pma_debug is True:
            print(url)
        contents = urlopen(url).read().decode("utf-8").strip("\"").strip("'")
        return contents
    except Exception as e:
        version = None

    url = pma._pma_join(pmaviewURL, "viewer/version")
    try:
        # Oops, perhaps this is a PMA.view 1.x version
        if pma._pma_debug is True:
            print(url)
        contents = urlopen(url).read().decode("utf-8").strip("\"").strip("'")
        return contents
    except Exception as e:
        version = None

    return version
