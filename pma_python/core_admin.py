import os
from pma_python import core, pma
from math import ceil
from PIL import Image
from random import choice
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
import requests

__version__ = pma.__version__


def set_debug_flag(flag):
    """
    Determine whether pma_python runs in debugging mode or not.
    When in debugging mode (flag = true), extra output is produced when certain conditions in the code are not met
    """
    pma._pma_set_debug_flag(flag)


def _pma_admin_url(sessionID=None):
    # let's get the base URL first for the specified session
    url = core._pma_url(sessionID)
    if url is None:
        # sort of a hopeless situation; there is no URL to refer to
        return None
    # remember, _pma_url is guaranteed to return a URL that ends with "/"
    return pma._pma_join(url, "admin/json/")


def _pma_check_for_pma_start(method="", url=None, session=None):
    if (core._pma_pmacoreliteSessionID == session):
        raise Exception("PMA.start doesn't support", method)
    elif (url == core._pma_pmacoreliteURL):
        if core.is_lite():
            raise ValueError("PMA.core.lite found running, but doesn't support an administrative back-end")
        else:
            raise ValueError(
                "PMA.core.lite not found, and besides; it doesn't support an administrative back-end anyway")


def _pma_http_post(url, data):
    if (pma._pma_debug is True):
        print("Posting to", url)
        print("   with payload", data)
    resp = requests.post(url, json=data)
    if pma._pma_debug is True and "code" in resp.text:
        print(resp.text)
    else:
        pma._pma_clear_url_cache()
    return resp.text


def admin_connect(pmacoreURL, pmacoreAdmUsername, pmacoreAdmPassword):
    """
    Attempt to connect to PMA.core instance; success results in a SessionID
    only success if the user has administrative status
    """
    _pma_check_for_pma_start("admin_connect", pmacoreURL)

    url = pma._pma_join(pmacoreURL, "admin/json/AdminAuthenticate?caller=SDK.Python")
    url += "&username=" + pma._pma_q(pmacoreAdmUsername)
    url += "&password=" + pma._pma_q(pmacoreAdmPassword)

    if (pma._pma_debug is True):
        print(url)

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
        core._pma_usernames[admSessionID] = pmacoreAdmUsername

        if not (admSessionID in core._pma_slideinfos):
            core._pma_slideinfos[admSessionID] = dict()
        core._pma_amount_of_data_downloaded[admSessionID] = len(loginresult)

    return (admSessionID)


def admin_disconnect(admSessionID=None):
    """
    Attempt to disconnect from PMA.core instance; True if valid admSessionID was indeed disconnected
    """
    return core.disconnect(admSessionID)


def send_email_reminder(admSessionID, login, subject="PMA.core password reminder"):
    """
    Send out an email reminder to the address associated with user login
    """
    reminderParams = {"username": login, "subject": subject, "messageTemplate": ""}
    url = _pma_admin_url(admSessionID) + "EmailPassword"
    reminderResponse = _pma_http_post(url, reminderParams)
    return reminderResponse


def add_user(admSessionID, login, firstName, lastName, email, pwd, canAnnotate=False, isAdmin=False, isSuspended=False):
    print("Using credentials from ", admSessionID)

    createUserParams = {
        "sessionID": admSessionID,
        "user": {
            "Login": login,
            "FirstName": firstName,
            "LastName": lastName,
            "Password": pwd,
            "Email": email,
            "Administrator": isAdmin,
            "CanAnnotate": canAnnotate,
            "Suspended": isSuspended
        }
    }
    url = _pma_admin_url(admSessionID) + "CreateUser"
    createUserResponse = _pma_http_post(url, createUserParams)
    return createUserResponse


def user_exists(admSessionID, u):
    from pma_python import pma
    url = (_pma_admin_url(admSessionID) + "SearchUsers?source=Local" + "&SessionID=" + pma._pma_q(admSessionID) + "&query=" + pma._pma_q(u))
    try:
        r = pma._pma_http_get(url, {'Accept': 'application/json'})
    except Exception as e:
        print(e)
        return None
    results = r.json()
    for usr in results:
        if usr["Login"].lower() == u.lower():
            return True
    return False


def create_amazons3_mounting_point(accessKey, secretKey, path, instanceId, chunkSize=1048576, serviceUrl=None):
    """
    create an Amazon S3 mounting point. A list of these is to be used to supply method create_root_directory()
    """
    createAmazonS3MountingPointParams = {
        "AccessKey": accessKey,
        "SecretKey": secretKey,
        "ChunkSize": chunkSize,
        "ServiceUrl": serviceUrl,
        "Path": path,
        "InstanceId": instanceId
    }
    return createAmazonS3MountingPointParams


def create_filesystem_mounting_point(username, password, domainName, path, instanceId):
    """
    create an FileSystem mounting point. A list of these is to be used to supply method create_root_directory()
    """
    createFileSystemMountingPointParams = {
        "Username": username,
        "Password": password,
        "DomainName": domainName,
        "Path": path,
        "InstanceId": instanceId
    }
    return createFileSystemMountingPointParams


def create_onedrive_mounting_point():
    """
    Placeholder for future functionality
    """
    return None


def create_dropbox_mounting_point():
    """
    Placeholder for future functionality
    """
    return None


def create_googledrive_mounting_point():
    """
    Placeholder for future functionality
    """
    return None


def create_root_directory(admSessionID,
                          alias,
                          amazonS3MountingPoints=None,
                          fileSystemMountingPoints=None,
                          description="Root dir created through pma_python",
                          isPublic=False,
                          isOffline=False):
    createRootDirectoryParams = {
        "sessionID": admSessionID,
        "rootDirectory": {
            "Alias": alias,
            "Description": description,
            "Public": isPublic,
            "Offline": isOffline,
            "AmazonS3MountingPoints": amazonS3MountingPoints,
            "FileSystemMountingPoints": fileSystemMountingPoints
        }
    }
    url = _pma_admin_url(admSessionID) + "CreateRootDirectory"
    createRootDirectoryReponse = requests.post(url, json=createRootDirectoryParams)
    return createRootDirectoryReponse.text


def create_directory(admSessionID, path):
    try:
        slides = core.get_slides(path)
        if pma._pma_debug is True:
            print("Directory already exists")
        return False
    except Exception:
        url = _pma_admin_url(admSessionID) + "CreateDirectory"
        result = _pma_http_post(url, {"sessionID": admSessionID, "path": path})

    try:
        return len(core.get_slides(path)) == 0
    except Exception:
        return False


def rename_directory(admSessionID, originalPath, newName):
    url = _pma_admin_url(admSessionID) + "RenameDirectory"
    payload = {"sessionID": admSessionID, "path": originalPath, "newName": newName}
    result = _pma_http_post(url, payload)
    if "Code" in result:
        if pma._pma_debug is True:
            print(result)
        return False
    return True


def delete_directory(admSessionID, path):
    url = _pma_admin_url(admSessionID) + "DeleteDirectory"
    payload = {
        "sessionID": admSessionID,
        "path": path,
    }
    result = _pma_http_post(url, payload)
    if "Code" in result:
        if pma._pma_debug is True:
            print(result)
        return False
    return True

def reverse_uid(admSessionID, slideRefUid):
    """
    lookup the reverse path of a UID for a specific slide
    """
    if (admSessionID == core._pma_pmacoreliteSessionID):
        if is_lite():
            raise ValueError(
                "PMA.core.lite found running, but doesn't support UIDs. For advanced anonymization, please upgrade to PMA.core."
            )
        else:
            raise ValueError(
                "PMA.core.lite not found, and besides; it doesn't support UIDs. For advanced anonymization, please upgrade to PMA.core."
            )
    url = _pma_admin_url(admSessionID) + "ReverseLookupUID?sessionID=" + pma._pma_q(admSessionID) + "&uid=" + pma._pma_q(slideRefUid)
    if (pma._pma_debug is True):
        print(url)
    r = requests.get(url)
    json = r.json()
    if ("Code" in json):
        raise Exception("reverse_uid on  " + slideRefUid + " resulted in: " + json["Message"])
    else:
        path = json
    return path

def reverse_root_directory(admSessionID, alias):
    """
    lookup the reverse path of a root-directory
    """
    if (admSessionID == core._pma_pmacoreliteSessionID):
        if is_lite():
            raise ValueError(
                "PMA.core.lite found running, but doesn't support this method."
            )
        else:
            raise ValueError(
                "PMA.core.lite not found, and besides; it doesn't support this method."
            )
    url = _pma_admin_url(admSessionID) + "ReverseLookupRootDirectory?sessionID=" + pma._pma_q(admSessionID) + "&alias=" + pma._pma_q(alias)
    if (pma._pma_debug is True):
        print(url)
    r = requests.get(url)
    json = r.json()
    if ("Code" in json):
        raise Exception("reverse_root_directory on  " + alias + " resulted in: " + json["Message"])
    else:
        path = json
    return path
