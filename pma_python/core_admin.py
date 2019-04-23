import os
from pma_python import core, pma
from math import ceil
from PIL import Image
from random import choice
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
from xml.dom import minidom
from pma_python import pma

import requests

__version__ = pma.__version__

def admin_connect(pmacoreURL, pmacoreAdmUsername, pmacoreAdmPassword):
    """
    Attempt to connect to PMA.core instance; success results in a SessionID
    only success if the user has administrative status
    """
    if (pmacoreURL == core._pma_pmacoreliteURL):
        if core.is_lite():
            raise ValueError ("PMA.core.lite found running, but doesn't support an administrative back-end")
        else:
            raise ValueError ("PMA.core.lite not found, and besides; it doesn't support an administrative back-end anyway")
            
    # purposefully DON'T use helper function _pma_api_url() here:    
    # why? Because_pma_api_url() takes session information into account (which we don't have yet)
    url = pma._pma_join(pmacoreURL, "admin/json/AdminAuthenticate?caller=SDK.Python") 
    url += "&username=" + pma._pma_q(pmacoreAdmUsername)
    url += "&password=" + pma._pma_q(pmacoreAdmPassword)
    
    try:
        headers = {'Accept': 'application/json'}
        # r = requests.get(url, headers=headers)
        r = pma._pma_http_get(url, headers)
    except Exception as e:
        print(e)
        return None        
    loginresult = r.json()

    # print(loginresult)
        
    if (str(loginresult["Success"]).lower() != "true"):
        admSessionID = None
    else:
        admSessionID = loginresult["SessionId"]
        
        core._pma_sessions[admSessionID] = pmacoreURL
        core._pma_usernames[admSessionID] = pmacoreUsername
		
        if not (admSessionID in core._pma_slideinfos):
            core._pma_slideinfos[admSessionID] = dict()
        core._pma_amount_of_data_downloaded[admSessionID] = len(loginresult)
    
    return (admSessionID)    

def admin_disconnect(admSessionID = None):
	"""
	Attempt to disconnect from PMA.core instance; True if valid admSessionID was indeed disconnected
	"""
	return core.disconnect(admSessionID)
