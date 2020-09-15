import os
import datetime
from math import ceil
from PIL import Image
from random import choice
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
from pma_python import pma

import requests
import shutil
import re
import pandas as pd
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

__version__ = pma.__version__

pma_annotation_source_format_pathomation = 0
pma_annotation_source_format_native = 1
pma_annotation_source_format_visiopharm = 2
pma_annotation_source_format_indicalabs = 3
pma_annotation_source_format_aperio = 4
pma_annotation_source_format_definiens = 4
pma_annotation_source_format_xml = 4

pma_annotation_target_format_pathomation = 2
pma_annotation_target_format_visiopharm = 0
pma_annotation_target_format_indicalabs = 1
pma_annotation_target_format_aperio = 3
pma_annotation_target_format_definiens = 3
pma_annotation_target_format_xml = 3
pma_annotation_target_format_csv = 4

# internal module helper variables and functions
_pma_sessions = dict()
_pma_usernames = dict()
_pma_slideinfos = dict()
_pma_pmacoreliteURL = "http://localhost:54001/"
_pma_pmacoreliteSessionID = "SDK.Python"
_pma_usecachewhenretrievingtiles = True
_pma_amount_of_data_downloaded = {_pma_pmacoreliteSessionID: 0}


def set_debug_flag(flag):
    """
    Determine whether Core module runs in debugging mode or not.
    When in debugging mode (flag = true), extra output is produced when certain conditions in the code are not met
    """
    pma._pma_set_debug_flag(flag)


def _pma_session_id(sessionID=None):
    if (sessionID is None):
        # if the sessionID isn't specified, maybe we can still recover it somehow
        return _pma_first_session_id()
    else:
        # nothing to do in this case; a SessionID WAS passed along, so just continue using it
        return sessionID


def _pma_first_session_id():
    # do we have any stored sessions from earlier login events?
    global _pma_sessions
    global _pma_slideinfos

    if (len(_pma_sessions.keys()) > 0):
        # yes we do! This means that when there's a PMA.core active session AND PMA.core.lite version running,
        # the PMA.core active will be selected and returned
        return list(_pma_sessions.keys())[0]
    else:
        # ok, we don't have stored sessions; not a problem per se...
        if (_pma_is_lite()):
            if (_pma_pmacoreliteSessionID not in _pma_slideinfos):
                # _pma_sessions[_pma_pmacoreliteSessionID] = _pma_pmacoreliteURL

                _pma_slideinfos[_pma_pmacoreliteSessionID] = dict()
            if (_pma_pmacoreliteSessionID not in _pma_amount_of_data_downloaded):
                _pma_amount_of_data_downloaded[_pma_pmacoreliteSessionID] = 0
            return _pma_pmacoreliteSessionID
        else:
            # no stored PMA.core sessions found NOR PMA.core.lite
            return None


def _pma_url(sessionID=None):
    sessionID = _pma_session_id(sessionID)
    if sessionID is None:
        # sort of a hopeless situation; there is no URL to refer to
        return None
    elif sessionID == _pma_pmacoreliteSessionID:
        return _pma_pmacoreliteURL
    else:
        # assume sessionID is a valid session; otherwise the following will generate an error
        if sessionID in _pma_sessions.keys():
            url = _pma_sessions[sessionID]
            if (not url.endswith("/")):
                url = url + "/"
            return url
        else:
            raise Exception("Invalid sessionID:" + str(sessionID))


def _pma_is_lite(pmacoreURL=_pma_pmacoreliteURL):
    """checks to see if PMA.core.lite (server component of PMA.start) is running at a given endpoint.
    if pmacoreURL is omitted, default check is to see if PMA.start is effectively running at localhost
    (defined by _pma_pmacoreliteURL). Note that PMA.start may not be running, while it is actually installed.
    This method doesn't detect whether PMA.start is installed; merely whether it's running!
    if pmacoreURL is specified, then the method checks if there's an instance of PMA.start (results in True),
    PMA.core (results in False) or nothing (at least not a Pathomation software platform component) at all
    (results in None)"""
    url = pma._pma_join(pmacoreURL, "api/json/IsLite")
    try:
        r = requests.get(url)
    except Exception as e:
        # this happens when NO instance of PMA.core is detected
        return None
    value = r.json()
    return value is True


def _pma_api_url(sessionID=None):
    # let's get the base URL first for the specified session
    url = _pma_url(sessionID)
    if url is None:
        # sort of a hopeless situation; there is no URL to refer to
        return None
    # remember, _pma_url is guaranteed to return a URL that ends with "/"
    return pma._pma_join(url, "api/json/")


def _pma_query_url(sessionID=None):
    # let's get the base URL first for the specified session
    url = _pma_url(sessionID)
    if url is None:
        # sort of a hopeless situation; there is no URL to refer to
        return None
    # remember, _pma_url is guaranteed to return a URL that ends with "/"
    return pma._pma_join(url, "query/json/")


# end internal module helper variables and functions


def is_lite(pmacoreURL=_pma_pmacoreliteURL):
    """
    Checks to see if PMA.core.lite (server component of PMA.start) is running at a given endpoint.
    if pmacoreURL is omitted, default check is to see if PMA.start is effectively running at localhost
    (defined by _pma_pmacoreliteURL).Note that PMA.start may not be running, while it is actually installed.
    This method doesn't detect whether PMA.start is installed; merely whether it's running!
    if pmacoreURL is specified, then the method checks if there's an instance of PMA.start (results in True),
    PMA.core (results in False) or nothing (at least not a Pathomation software platform component) at all
    (results in None)
    """
    return _pma_is_lite(pmacoreURL)


def get_version_info(pmacoreURL=_pma_pmacoreliteURL):
    """
    Get version info from PMA.core instance running at pmacoreURL.
    Return None if PMA.core not found running at pmacoreURL endpoint
    """
    # purposefully DON'T use helper function _pma_api_url() here:
    # why? because GetVersionInfo can be invoked WITHOUT a valid SessionID;
    # _pma_api_url() takes session information into account

    url = pma._pma_join(pmacoreURL, "api/json/GetVersionInfo")
    if pma._pma_debug == True:
        print(url)

    try:
        r = requests.get(url)
    except Exception:
        return None

    json = r.json()
    version = None
    if ("Code" in json):
        raise Exception("get version info resulted in: " + json["Message"])
    elif ("d" in json):
        version = json["d"]
    else:
        version = json

    return version


def get_api_version(pmacoreURL=_pma_pmacoreliteURL):
    url = pma._pma_join(pmacoreURL, "api/json/GetAPIVersion")
    if pma._pma_debug == True:
        print(url)

    try:
        r = requests.get(url)
    except Exception:
        return None

    try:
        json = r.json()
    except Exception:
        raise Exception("GetAPIVersion method not available at " + pmacoreURL)

    version = None
    if ("Code" in json):
        raise Exception("get_api_version resulted in: " + json["Message"])
    elif ("d" in json):
        version = json["d"]
    else:
        version = json

    return version


def get_api_verion_string(pmacoreURL=_pma_pmacoreliteURL):
    v = get_api_version(pmacoreURL)
    return ".".join([str(x) for x in v])


def connect(pmacoreURL=_pma_pmacoreliteURL, pmacoreUsername="", pmacorePassword=""):
    """
    Attempt to connect to PMA.core instance; success results in a SessionID
    """
    global _pma_sessions  # so afterwards we can look up what username actually belongs to a sessions
    global _pma_usernames  # so afterwards we can determine the PMA.core URL to connect to for a given SessionID
    global _pma_slideinfos  # a caching mechanism for slide information; obsolete and should be improved
    global _pma_amount_of_data_downloaded  # keep track of how much data was downloaded

    if (pmacoreURL == _pma_pmacoreliteURL):
        if is_lite():
            # no point authenticating localhost / PMA.core.lite
            sessionID = _pma_pmacoreliteSessionID
            _pma_sessions[sessionID] = pmacoreURL
            if not (sessionID in _pma_slideinfos):
                _pma_slideinfos[sessionID] = {}
            _pma_amount_of_data_downloaded[sessionID] = 0
            return sessionID
        else:
            return None

    # purposefully DON'T use helper function _pma_api_url() here:
    # why? Because_pma_api_url() takes session information into account (which we don't have yet)
    url = pma._pma_join(pmacoreURL, "api/json/authenticate?caller=SDK.Python")
    if (pmacoreUsername != ""):
        url += "&username=" + pma._pma_q(pmacoreUsername)
        if (pma._pma_debug is True):
            print("Authenticating via", url + "&password=TOP_SECRET")
    if (pmacorePassword != ""):
        url += "&password=" + pma._pma_q(pmacorePassword)

    try:
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)
    except Exception as e:
        print(e)
        return None

    loginresult = r.json()

    if (str(loginresult["Success"]).lower() != "true"):
        sessionID = None
    else:
        sessionID = loginresult["SessionId"]

        _pma_usernames[sessionID] = pmacoreUsername
        _pma_sessions[sessionID] = pmacoreURL
        if not (sessionID in _pma_slideinfos):
            _pma_slideinfos[sessionID] = {}
        _pma_amount_of_data_downloaded[sessionID] = len(loginresult)

    return sessionID


def disconnect(sessionID=None):
    """
    Attempt to disconnect from a PMA.core instance
    """
    sessionID = _pma_session_id(sessionID)
    url = _pma_api_url(sessionID) + "DeAuthenticate?sessionID=" + pma._pma_q((sessionID))
    contents = urlopen(url).read()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(contents)
    if (len(_pma_sessions.keys()) > 0):
        # yes we do! This means that when there's a PMA.core active session AND PMA.core.lite version running,
        # the PMA.core active will be selected and returned
        del _pma_sessions[sessionID]
        del _pma_slideinfos[sessionID]
    return True


def get_root_directories(sessionID=None):
    """
    Return an array of root-directories available to sessionID
    """
    sessionID = _pma_session_id(sessionID)
    url = _pma_api_url(sessionID) + "GetRootDirectories?sessionID=" + pma._pma_q((sessionID))
    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("get_root_directories failed with error " + json["Message"])
    return json


def _pma_merge_dict_values(dicts):
    res = []
    for (_, lst) in dicts.items():
        for el in lst:
            el = str(el)
            if el not in res:
                res.append(el)
    return res


def analyse_corresponding_root_directories(sessionIDs):
    """
    Return a pandas DataFrame that indicates which root-directories exist on which PMA.core instances
    """
    # create a dictionary all_rds that contains a list of all root-directories per sessionID
    all_rds = {}
    all_urls = []
    for sess in sessionIDs:
        url = who_am_i(sess)["url"]
        all_urls.append(url)
        rds = get_root_directories(sess)
        all_rds[url] = rds
    # pp.pprint(all_rds)

    # create a linear list to use as index a pandas DataFrame.
    # This list contains ALL root-directories, regardless of the PMA.core instance where they occur
    root_dirs = _pma_merge_dict_values(all_rds)

    # create a blank DataFrame; rows = root-directories; columns = PMA.core instances
    df = pd.DataFrame(index=root_dirs, columns=all_urls)

    # fill up the cells in the DataFrame with True or False,
    # depending on whether the root-dir exists at a specific instance
    for rd in root_dirs:
        for url in all_urls:
            for el in all_rds[url]:
                if str(el) == str(rd):
                    df.loc[rd][url] = True
                    break
            if not (df.loc[rd][url] is True):
                df.loc[rd][url] = False

    # Add a aggregation colums that indicates how many times a specific root-dir was found across all sessionIDs
    df["count"] = (df is True).sum(axis=1)
    return df


def get_directories(startDir, sessionID=None, recursive=False):
    """
    Return an array of sub-directories available to sessionID in the startDir directory
    """
    sessionID = _pma_session_id(sessionID)
    url = _pma_api_url(sessionID) + "GetDirectories?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(startDir)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("get_directories to " + startDir + " resulted in: " + json["Message"])
    elif ("d" in json):
        dirs = json["d"]
    else:
        dirs = json

    # handle recursion, if so desired
    if (type(recursive) == bool and recursive is True) or (type(recursive) == int and recursive > 0):
        for dir in get_directories(startDir, sessionID):
            if type(recursive) == bool:
                dirs = dirs + get_directories(dir, sessionID, recursive)
            elif type(recursive) == int:
                dirs = dirs + get_directories(dir, sessionID, recursive - 1)

    return dirs


def get_first_non_empty_directory(startDir=None, sessionID=None):
    sessionID = _pma_session_id(sessionID)

    if ((startDir is None) or (startDir == "")):
        startDir = "/"

    slides = None
    try:
        slides = get_slides(startDir=startDir, sessionID=sessionID)
    except Exception:
        if pma._pma_debug == True:
            print("Unable to examine", startDir)
        if (startDir != "/"):
            return slides

    if ((slides is not None) and (len(slides) > 0)):
        return startDir
    else:
        if (startDir == "/"):
            for dir in get_root_directories(sessionID=sessionID):
                nonEmtptyDir = get_first_non_empty_directory(startDir=dir, sessionID=sessionID)
                if (not (nonEmtptyDir is None)):
                    return nonEmtptyDir
        else:
            try:
                dirs = get_directories(startDir, sessionID)
            except Exception:
                if pma._pma_debug == True:
                    print("Unable to examine", startDir)
            else:
                for dir in dirs:
                    nonEmtptyDir = get_first_non_empty_directory(startDir=dir, sessionID=sessionID)
                    if (not (nonEmtptyDir is None)):
                        return nonEmtptyDir
    return None


def get_slides(startDir, sessionID=None, recursive=False):
    """
    Return an array of slides available to sessionID in the startDir directory
    """
    sessionID = _pma_session_id(sessionID)
    if (startDir.startswith("/")):
        startDir = startDir[1:]
    url = _pma_api_url(sessionID) + "GetFiles?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(startDir)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("get_slides from " + startDir + " resulted in: " + json["Message"])
    elif ("d" in json):
        slides = json["d"]
    else:
        slides = json

    # handle recursion, if so desired
    if (type(recursive) == bool and recursive is True) or (type(recursive) == int and recursive > 0):
        for dir in get_directories(startDir, sessionID):
            if type(recursive) == bool:
                slides = slides + get_slides(dir, sessionID, recursive)
            elif type(recursive) == int:
                slides = slides + get_slides(dir, sessionID, recursive - 1)

    return slides


def analyse_corresponding_slides(sessionPathDict, recursive=False, includeFingerprint=False):
    """
    Return a pandas DataFrame that indicates which slides exist on which PMA.core instances
    :param dict sessionPathDict: a dictionary that looks e.g. like
           {DevSessionID: rootDirAndPath1, ProdSessionID: rootDirAndPath2 }
    :param bool recursive: indicates whether the method should look in sub-directories or not
    """

    all_slides = {}
    all_urls = []
    for (sessionID, path) in sessionPathDict.items():
        if (path[-1:]) != "/":
            path = path + "/"
        url = who_am_i(sessionID)["url"] + "[" + path + "]"
        all_urls.append(url)
        slides = get_slides(path, recursive=recursive, sessionID=sessionID)
        slides = [sl.replace(path, ".../") for sl in slides]
        all_slides[url] = slides

    final_slide_list = _pma_merge_dict_values(all_slides)

    df = pd.DataFrame(index=final_slide_list, columns=all_urls)

    for sl in final_slide_list:
        for url in all_urls:
            for el in all_slides[url]:
                if str(sl) == str(el):
                    df.loc[sl][url] = True
                    break
            if not (df.loc[sl][url] is True):
                df.loc[sl][url] = False

    df["count"] = (df is True).sum(axis=1)

    if includeFingerprint is True:
        slides_to_check = df[df["count"] == len(all_urls)]
        num_urls = len(all_urls)
        print("Number of URLs: ", num_urls)

    return df


def get_slide_file_extension(slideRef):
    """
    Determine the file extension for this slide
    """
    return os.path.splitext(slideRef)[-1]


def get_slide_file_name(slideRef):
    """
    Determine the file name (with extension) for this slide
    """
    return os.path.basename(slideRef)


def get_uid(slideRef, sessionID=None):
    """
    Get the UID for a specific slide
    """
    sessionID = _pma_session_id(sessionID)
    if (sessionID == _pma_pmacoreliteSessionID):
        if is_lite():
            raise ValueError(
                "PMA.core.lite found running, but doesn't support UID generation.For advanced anonymization, please upgrade to PMA.core."
            )
        else:
            raise ValueError(
                "PMA.core.lite not found, and besides; it doesn't support UID generation. For advanced anonymization, please upgrade to PMA.core."
            )

    url = _pma_api_url(sessionID) + "GetUID?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(slideRef)
    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("get_uid on  " + slideRef + " resulted in: " + json["Message"])
    else:
        uid = json
    return uid


def get_fingerprint(slideRef, sessionID=None):
    """
    Get the fingerprint for a specific slide
    """
    sessionID = _pma_session_id(sessionID)
    url = _pma_api_url(sessionID) + "GetFingerprint?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)

    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("get_fingerprint on  " + slideRef + " resulted in: " + json["Message"])
    else:
        fingerprint = json
    return fingerprint


def who_am_i(sessionID=None):
    """
    Getting information about your Session
    """
    sessionID = _pma_session_id(sessionID)
    retval = None

    if (sessionID == _pma_pmacoreliteSessionID):
        retval = {
            "sessionID": _pma_pmacoreliteSessionID,
            "username": None,
            "url": _pma_pmacoreliteURL,
            "amountOfDataDownloaded": _pma_amount_of_data_downloaded[_pma_pmacoreliteSessionID]
        }
    elif (sessionID is not None):
        retval = {
            "sessionID": sessionID,
            "username": _pma_usernames[sessionID],
            "url": _pma_url(sessionID),
            "amountOfDataDownloaded": _pma_amount_of_data_downloaded[sessionID]
        }

    return retval


def sessions():
    global _pma_sessions
    return _pma_sessions


def get_tile_size(sessionID=None):
    sessionID = _pma_session_id(sessionID)
    global _pma_slideinfos
    if (len(_pma_slideinfos[sessionID]) < 1):
        dir = get_first_non_empty_directory(sessionID)
        slides = get_slides(dir, sessionID)
        info = get_slide_info(slides[0], sessionID)
    else:
        info = choice(list(_pma_slideinfos[sessionID].values()))

    return (int(info["TileSize"]), int(info["TileSize"]))


def get_slide_info(slideRef, sessionID=None):
    """
    Return raw image information in the form of nested dictionaries
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]

    global _pma_slideinfos

    if (not (slideRef in _pma_slideinfos[sessionID])):
        url = _pma_api_url(sessionID) + "GetImageInfo?SessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)
        if pma._pma_debug == True:
            print(url)
        r = requests.get(url)
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("ImageInfo to " + slideRef + " resulted in: " + json["Message"])
        elif ("d" in json):
            _pma_slideinfos[sessionID][slideRef] = json["d"]
        else:
            _pma_slideinfos[sessionID][slideRef] = json
    elif pma._pma_debug == True:
        print("Getting slide info from cache")

    return _pma_slideinfos[sessionID][slideRef]


def get_max_zoomlevel(slideRef, sessionID=None):
    """
    Determine the maximum zoomlevel that still represents an optical magnification
    """
    info = get_slide_info(slideRef, sessionID)
    if (info is None):
        print("Unable to get information for", slideRef, " from ", sessionID)
        return 0
    else:
        if ("MaxZoomLevel" in info):
            try:
                return int(info["MaxZoomLevel"])
            except Exception:
                print("Something went wrong consulting the MaxZoomLevel key in info{} dictionary; value =",
                      info["MaxZoomLevel"])
                return 0
        else:
            try:
                return int(info["NumberOfZoomLevels"])
            except Exception:
                print("Something went wrong consulting the NumberOfZoomLevels key in info{} dictionary; value =",
                      info["NumberOfZoomLevels"])
                return 0


def get_zoomlevels_list(slideRef, sessionID=None, min_number_of_tiles=0):
    """
    Obtain a list with all zoomlevels, starting with 0 and up to and including max_zoomlevel
    Use min_number_of_tiles argument to specify that you're only interested in zoomlevels that include at lease a given number of tiles
    """
    return sorted(list(get_zoomlevels_dict(slideRef, sessionID, min_number_of_tiles).keys()))


def get_zoomlevels_dict(slideRef, sessionID=None, min_number_of_tiles=0):
    """
    Obtain a dictionary with the number of tiles per zoomlevel.
    Information is returned as (x, y, n) tupels per zoomlevel, with
        x = number of horizontal tiles,
        y = number of vertical tiles,
        n = total number of tiles at specified zoomlevel (x * y)
    Use min_number_of_tiles argument to specify that you're only interested in zoomlevels that include at lease a given number of tiles
    """
    zoomlevels = list(range(0, get_max_zoomlevel(slideRef, sessionID) + 1))
    dimensions = [
        get_number_of_tiles(slideRef, z, sessionID) for z in zoomlevels
        if get_number_of_tiles(slideRef, z, sessionID)[2] > min_number_of_tiles
    ]
    d = dict(zip(zoomlevels[-len(dimensions):], dimensions))

    return d


def get_pixels_per_micrometer(slideRef, zoomlevel=None, sessionID=None):
    """
    Retrieve the physical dimension in terms of pixels per micrometer.
    When zoomlevel is left to its default value of None, dimensions at the highest zoomlevel are returned
    (in effect returning the "native" resolution at which the slide was registered)
    """
    maxZoomLevel = get_max_zoomlevel(slideRef, sessionID)
    info = get_slide_info(slideRef, sessionID)
    xppm = info["MicrometresPerPixelX"]
    yppm = info["MicrometresPerPixelY"]
    if (zoomlevel is None or zoomlevel == maxZoomLevel):
        return (float(xppm), float(yppm))
    else:
        factor = 2**(zoomlevel - maxZoomLevel)
        return (float(xppm) / factor, float(yppm) / factor)


def get_pixel_dimensions(slideRef, zoomlevel=None, sessionID=None):
    """Get the total dimensions of a slide image at a given zoomlevel"""
    maxZoomLevel = get_max_zoomlevel(slideRef, sessionID)
    info = get_slide_info(slideRef, sessionID)
    if (zoomlevel is None or zoomlevel == maxZoomLevel):
        return (int(info["Width"]), int(info["Height"]))
    else:
        factor = 2**(zoomlevel - maxZoomLevel)
        return (int(info["Width"]) * factor, int(info["Height"]) * factor)


def get_number_of_tiles(slideRef, zoomlevel=None, sessionID=None):
    """Determine the number of tiles needed to reconstitute a slide at a given zoomlevel"""
    pixels = get_pixel_dimensions(slideRef, zoomlevel, sessionID)
    sz = get_tile_size(sessionID)
    xtiles = int(ceil(pixels[0] / sz[0]))
    ytiles = int(ceil(pixels[1] / sz[0]))
    ntiles = xtiles * ytiles
    return (xtiles, ytiles, ntiles)


def get_physical_dimensions(slideRef, sessionID=None):
    """Determine the physical dimensions of the sample represented by the slide.
    This is independent of the zoomlevel: the physical properties don't change because the magnification changes"""
    ppmData = get_pixels_per_micrometer(slideRef, sessionID)
    pixelSz = get_pixel_dimensions(slideRef, sessionID)
    return (pixelSz[0] * ppmData[0], pixelSz[1] * ppmData[1])


def get_number_of_channels(slideRef, sessionID=None):
    """Number of fluorescent channels for a slide (when slide is brightfield, return is always 1)"""
    info = get_slide_info(slideRef, sessionID)
    channels = info["TimeFrames"][0]["Layers"][0]["Channels"]
    return len(channels)


def get_number_of_layers(slideRef, sessionID=None):
    """Number of (z-stacked) layers for a slide"""
    info = get_slide_info(slideRef, sessionID)
    layers = info["TimeFrames"][0]["Layers"]
    return len(layers)


def get_number_of_z_stack_layers(slideRef, sessionID=None):
    return get_number_of_layers(slideRef, sessionID)


def is_fluorescent(slideRef, sessionID=None):
    """Determine whether a slide is a fluorescent image or not"""
    return get_number_of_channels(slideRef, sessionID) > 1


def is_multi_layer(slideRef, sessionID=None):
    """Determine whether a slide contains multiple (stacked) layers or not"""
    return get_number_of_layers(slideRef, sessionID) > 1


def get_last_modified_date(slideRef, sessionID=None):
    info = get_slide_info(slideRef, sessionID)
    lms = info["LastModified"].strip("/").replace("Date(", "").replace(")", "")
    return datetime.datetime.fromtimestamp(int(lms) / 1000.0)


def is_z_stack(slideRef, sessionID=None):
    """Determine whether a slide is a z-stack or not"""
    return is_multi_layer(slideRef, sessionID)


def get_magnification(slideRef, zoomlevel=None, exact=False, sessionID=None):
    """Get the magnification represented at a certain zoomlevel"""
    ppm = get_pixels_per_micrometer(slideRef, zoomlevel, sessionID)[0]
    if (ppm > 0):
        if (exact is True):
            return round(40 / (ppm / 0.25))
        else:
            return round(40 / round(ppm / 0.25))
    else:
        return 0


def get_barcode_url(slideRef, sessionID=None):
    """Get the URL that points to the barcode (alias for "label") for a slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = (_pma_url(sessionID) + "barcode" + "?SessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef))
    return url

def get_barcode_image(slideRef, sessionID=None):
    """Get the barcode (alias for "label") image for a slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    r = requests.get(get_barcode_url(slideRef, sessionID))
    img = Image.open(BytesIO(r.content))
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(r.content)
    return img

def get_barcode_text(slideRef, sessionID=None):
    """Get the text encoded by the barcode (if there IS a barcode on the slide to begin with)"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = _pma_api_url(sessionID) + "GetBarcodeText?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_barcode_text on  " + slideRef + " resulted in: " + json["Message"])
        else:
            barcode = json
    else:
        barcode = ""
    return barcode

def get_label_url(slideRef, sessionID=None):
    """Get the URL that points to the label for a slide"""
    return get_barcode_url(slideRef, sessionID)

def get_label_image(slideRef, sessionID=None):
    """Get the label image for a slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    r = requests.get(get_label_url(slideRef, sessionID))
    img = Image.open(BytesIO(r.content))
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(r.content)
    return img

def get_thumbnail_url(slideRef, width=None, height=None, sessionID=None):
    """Get the URL that points to the thumbnail for a slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = (_pma_url(sessionID) + "thumbnail" + "?SessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef))
    if not (width is None):
        url = url + "&w=" + str(width)
    if not (height is None):
        url = url + "&h=" + str(height)
    return url

def get_thumbnail_image(slideRef, width=None, height=None, sessionID=None):
    """Get the thumbnail image for a slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = get_thumbnail_url(slideRef, width, height, sessionID)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    img = Image.open(BytesIO(r.content))
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(r.content)
    return img

def get_tile(slideRef, x=0, y=0, zoomlevel=None, zstack=0, sessionID=None, format="jpg", quality=100):
    """
    Get a single tile at position (x, y)
    Format can be 'jpg' or 'png'
    Quality is an integer value and varies from 0 (as much compression as possible; not recommended) to 100 (100%, no compression)
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    if (zoomlevel is None):
        zoomlevel = 0  # get_max_zoomlevel(slideRef, sessionID)

    url = _pma_url(sessionID) + "tile"
    if url is None:
        raise Exception("Unable to determine the PMA.core instance belonging to " + str(sessionID))

    params = {
        "sessionID": sessionID,
        "channels": 0,
        "timeframe": 0,
        "layer": int(round(zstack)),
        "pathOrUid": slideRef,
        "x": int(round(x)),
        "y": int(round(y)),
        "z": int(round(zoomlevel)),
        "format": format,
        "quality": quality,
        "cache": str(_pma_usecachewhenretrievingtiles).lower()
    }

    if pma._pma_debug == True:
        print(url)

    r = requests.get(url, params=params)
    img = Image.open(BytesIO(r.content))
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(r.content)
    return img

def get_region(slideRef, x=0, y=0, width=0, height=0, scale=1, zstack=0, sessionID=None, format="jpg", quality=100, rotation=0):
    """
    Gets a region of the slide at the specified scale 
    Format can be 'jpg' or 'png'
    Quality is an integer value and varies from 0 (as much compression as possible; not recommended) to 100 (100%, no compression)
    x,y,width,height is the region to get
    rotation is the rotation in degrees of the slide to get
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]

    url = _pma_url(sessionID) + "region"
    if url is None:
        raise Exception(
            "Unable to determine the PMA.core instance belonging to " + str(sessionID))

    params = {
        "sessionID": sessionID,
        "channels": 0,
        "timeframe": 0,
        "layer": int(round(zstack)),
        "pathOrUid": slideRef,
        "x": int(round(x)),
        "y": int(round(y)),
        "width": int(round(width)),
        "height": int(round(height)),
        "scale": float(scale),
        "format": format,
        "quality": quality,
        "rotation": float(rotation),
    }

    if pma._pma_debug == True:
        print(url)

    r = requests.get(url, params=params)
    img = Image.open(BytesIO(r.content))
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(r.content)
    return img


def get_submitted_forms(slideRef, sessionID=None):
    """Find out what forms where submitted for a specific slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = _pma_api_url(sessionID) + "GetFormSubmissions?sessionID=" + pma._pma_q(sessionID) + "&pathOrUids=" + pma._pma_q(slideRef)
    all_forms = get_available_forms(slideRef, sessionID)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"])
        else:
            data = json
            forms = {}
            for entry in data:
                if (not (entry["FormID"] in forms)):
                    forms[entry["FormID"]] = all_forms[entry["FormID"]]
            # should probably do some post-processing here, but unsure what that would actually be??
    else:
        forms = ""
    return forms


def get_submitted_form_data(slideRef, sessionID=None):
    """Get all submitted form data associated with a specific slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    url = _pma_api_url(sessionID) + "GetFormSubmissions?sessionID=" + pma._pma_q(sessionID) + "&pathOrUids=" + pma._pma_q(slideRef)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"])
        else:
            data = json
            # should probably do some post-processing here, but unsure what that would actually be??
    else:
        data = ""
    return data


def get_available_forms(slideRef=None, sessionID=None):
    """
    See what forms are available to fill out, either system-wide (leave slideref to None), or for a particular slide
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef is not None):
        if (slideRef.startswith("/")):
            slideRef = slideRef[1:]
        dir = os.path.split(slideRef)[0]
        url = _pma_api_url(sessionID) + "GetForms?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(dir)
    else:
        url = _pma_api_url(sessionID) + "GetForms?sessionID=" + pma._pma_q(sessionID)

    if pma._pma_debug == True:
        print(url)

    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"])
        else:
            forms_json = json
            forms = {}
            for entry in forms_json:
                forms[entry["Key"]] = entry["Value"]
    else:
        forms = ""
    return forms


def prepare_form_dictionary(formID, sessionID=None):
    """Prepare a form-dictionary that can be used later on to submit new form data for a slide"""
    if (formID is None):
        return None
    sessionID = _pma_session_id(sessionID)
    url = _pma_api_url(sessionID) + "GetFormDefinitions?sessionID=" + pma._pma_q(sessionID)
    if pma._pma_debug == True:
        print(url)
    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_available_forms on  " + formID + " resulted in: " + json["Message"])
        else:
            forms_json = json
            form_def = {}
            for form in forms_json:
                if ((form["FormID"] == formID) or (form["FormName"] == formID)):
                    for field in form["FormFields"]:
                        form_def[field["Label"]] = None
    else:
        form_def = ""
    return form_def


def submit_form_data(slideRef, formID, formDict, sessionID=None):
    """Not implemented yet"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef is not None):
        if (slideRef.startswith("/")):
            slideRef = slideRef[1:]
    return None


def get_annotations(slideRef, sessionID=None):
    """
    Retrieve the annotations for slide slideRef
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    dir = os.path.split(slideRef)[0]
    url = _pma_api_url(sessionID) + "GetAnnotations?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)
    if pma._pma_debug == True:
        print(url)

    r = requests.get(url)
    if ((not (r.text is None)) and (len(r.text) > 0)):
        json = r.json()
        global _pma_amount_of_data_downloaded
        _pma_amount_of_data_downloaded[sessionID] += len(json)
        if ("Code" in json):
            raise Exception("get_annotations() on  " + slideRef + " resulted in: " + json["Message"])
        else:
            annotations = json
    else:
        annotations = ""
    return annotations

def export_annotations(slideRef, annotation_source_format = [pma_annotation_source_format_pathomation], annotation_target_format = pma_annotation_target_format_xml, sessionID=None):
    """
    Retrieve the annotations for slide slideRef
    """
    sessionID = _pma_session_id(sessionID)
    if (not(isinstance(annotation_source_format, list))):
        annotation_source_format = [str(annotation_source_format)]
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    source_format = "&source=" + pma._pma_q(",".join(annotation_source_format))
    tgt_format = "&format=" + pma._pma_q(str(annotation_target_format))
    url = _pma_api_url(sessionID) + "ExportAnnotations?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef) + tgt_format + source_format
    if (pma._pma_debug is True):
        print(url)

    r = requests.get(url)

    if (r.ok):
        return BytesIO(r.content)
    else:
        raise ValueError("Unable to get annotations ("+str(r.status_code)+")")
    return None
	
def get_tiles(slideRef,
              fromX=0,
              fromY=0,
              toX=None,
              toY=None,
              zoomlevel=None,
              zstack=0,
              sessionID=None,
              format="jpg",
              quality=100):
    """
    Get all tiles with a (fromX, fromY, toX, toY) rectangle. Navigate left to right, top to bottom
    Format can be 'jpg' or 'png'
    Quality is an integer value and varies from 0 (as much compression as possible; not recommended) to 100 (100%, no compression)
    """
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]

    if (zoomlevel is None):
        zoomlevel = 0  # get_max_zoomlevel(slideRef, sessionID)
    if (toX is None):
        toX = get_number_of_tiles(slideRef, zoomlevel, sessionID)[0]
    if (toY is None):
        toY = get_number_of_tiles(slideRef, zoomlevel, sessionID)[1]
    for x in range(fromX, toX):
        for y in range(fromY, toY):
            yield get_tile(slideRef=slideRef,
                           x=x,
                           y=y,
                           zstack=zstack,
                           zoomlevel=zoomlevel,
                           sessionID=sessionID,
                           format=format,
                           quality=quality)


def show_slide(slideRef, sessionID=None):
    """Launch the default webbrowser and load a web-based viewer for the slide"""
    sessionID = _pma_session_id(sessionID)
    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]
    if (os.name == "posix"):
        os_cmd = "open "
    else:
        os_cmd = "start "

    if (sessionID == _pma_pmacoreliteSessionID):
        url = "http://free.pathomation.com/pma-view-lite/?path=" + pma._pma_q(slideRef)
    else:
        url = _pma_url(sessionID)
        if url is None:
            raise Exception("Unable to determine the PMA.core instance belonging to " + str(sessionID))
        else:
            url += ("viewer/index.htm" + "?sessionID=" + pma._pma_q(sessionID) + "^&pathOrUid=" + pma._pma_q(slideRef)
                    )  # note the ^& to escape a regular &

    if (pma._pma_debug == True):
        print(url)
    os.system(os_cmd + url)


def get_files_for_slide(slideRef, sessionID=None):
    """Obtain all files actually associated with a specific slide
    This is most relevant with slides that are defined by multiple files, like MRXS or VSI"""
    sessionID = _pma_session_id(sessionID)

    if (slideRef.startswith("/")):
        slideRef = slideRef[1:]

    if (sessionID == _pma_pmacoreliteSessionID):
        url = _pma_api_url(sessionID) + "EnumerateAllFilesForSlide?sessionID=" + pma._pma_q(
            sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)
    else:
        url = _pma_api_url(sessionID) + "getfilenames?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)

    if pma._pma_debug == True:
        print(url)

    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("enumerate_files_for_slide on  " + slideRef + " resulted in: " + json["Message"])
    elif ("d" in json):
        files = json["d"]
    else:
        files = json

    retval = {}
    for file in files:
        if (sessionID == _pma_pmacoreliteSessionID):
            retval[file] = {"Size": 0, "LastModified": None}
        else:
            retval[file["Path"]] = {"Size": file["Size"], "LastModified": file["LastModified"]}

    return retval


def search_slides(startDir, pattern, sessionID=None):
    sessionID = _pma_session_id(sessionID)
    if (sessionID == _pma_pmacoreliteSessionID):
        if is_lite():
            raise ValueError("PMA.core.lite found running, but doesn't support searching.")
        else:
            raise ValueError("PMA.core.lite not found, and besides; it doesn't support searching.")

    if (startDir.startswith("/")):
        startDir = startDir[1:]

    url = _pma_query_url(sessionID) + "Filename?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(
        startDir) + "&pattern=" + pma._pma_q(pattern)
    if pma._pma_debug == True:
        print("url =", url)

    r = requests.get(url)
    json = r.json()
    global _pma_amount_of_data_downloaded
    _pma_amount_of_data_downloaded[sessionID] += len(json)
    if ("Code" in json):
        raise Exception("search_slides on  " + startDir + " resulted in: " + json["Message"])
    elif ("d" in json):
        files = json["d"]
    else:
        files = json
    return files


def _pma_upload_callback(monitor, filename):
    v = monitor.bytes_read / monitor.len
    if not monitor.previous or v - monitor.previous > 0.05 or (v - monitor.previous > 0 and monitor.bytes_read == monitor.len):
        print("{0:.0%}".format(monitor.bytes_read / monitor.len))
        monitor.previous = v


def upload(local_source_slide, target_folder, target_pma_core_sessionID, callback=None):
    """
        Uploads a slide to a PMA.core server. Requires a PMA.start installation
        :param str local_source_slide: The local PMA.start relative file to upload
        :param str target_folder: The root directory and path to upload to the PMA.core server
        :param str target_pma_core_sessionID: A valid session id for a PMA.core server
        :param function|boolean callback: If True a default progress will be printed.
               If a function is passed it will be called for progress on each file upload.
               The function has the following signature:
                        `callback(bytes_read, bytes_length, filename)`
    """
    if not _pma_is_lite():
        raise Exception("No PMA.start found on localhost. Are you sure it is running?")

    if not target_folder:
        raise ValueError("target_folder cannot be empty")

    if (target_folder.startswith("/")):
        target_folder = target_folder[1:]

    files = get_files_for_slide(local_source_slide, _pma_pmacoreliteSessionID)
    sessionID = _pma_session_id(target_pma_core_sessionID)
    url = _pma_url(sessionID) + "transfer/Upload?sessionID=" + pma._pma_q(sessionID)

    if pma._pma_debug == True:
        print(url)

    mainDirectory = ''
    for i, f in enumerate(files):
        md = os.path.dirname(f)
        if i == 0 or len(md) < len(mainDirectory):
            mainDirectory = md

    uploadFiles = []
    for i, filepath in enumerate(files):
        s = os.path.getsize(filepath)
        if s > 0:
            uploadFiles.append({
                "Path": filepath.replace(mainDirectory, '').strip("\\").strip('/'),
                "Length": s,
                "IsMain": i == len(files) - 1,
                "FullPath": filepath
            })

    data = {"Path": target_folder, "Files": uploadFiles}

    uploadHeaderResponse = requests.post(url, json=data)
    if not uploadHeaderResponse.status_code == 200:
        raise Exception(uploadHeaderResponse.json()["Message"])

    uploadHeader = uploadHeaderResponse.json()

    pmaCoreUploadUrl = _pma_url(sessionID) + "transfer/Upload/" + pma._pma_q(
        uploadHeader["Id"]) + "?sessionID=" + pma._pma_q(sessionID) + "&path={0}"

    isAmazonUpload = True
    if not uploadHeader['Urls']:
        isAmazonUpload = False
        uploadHeader['Urls'] = [pmaCoreUploadUrl.format(f["Path"]) for f in uploadFiles]

    for i, f in enumerate(uploadFiles):
        uploadUrl = uploadHeader['Urls'][i]

        e = MultipartEncoder(
            fields={"file": (os.path.basename(f["Path"]), open(f["FullPath"], 'rb'), 'application/octet-stream')})

        _callback = None
        if callback is True:
            print("Uploading file: {0}".format(e.fields["file"][0]))
            _callback = lambda x: _pma_upload_callback(monitor, e.fields["file"][0])
        elif callable(callback):
            _callback = lambda x: callback(x.bytes_read, x.len, e.fields["file"][0])

        monitor = MultipartEncoderMonitor(e, _callback)

        monitor.previous = 0

        r = None
        if not isAmazonUpload:
            r = requests.post(uploadUrl, data=monitor, headers={'Content-Type': monitor.content_type})
        else:
            r = requests.put(uploadUrl, data=monitor, headers={'Content-Type': monitor.content_type})

        if not r.status_code == 200:
            raise Exception("Error uploading file {0}: {1}".format(f["Path"], r.json()["Message"]))


def download(slideRef, save_directory=None, sessionID=None):
    """
        Downloads a slide from a PMA.core server.
        :param str slideRef: The virtual path to the slide
        :param str save_directory: The local directory to save the downloaded files to
        :param str sessionID: The sessionID to authenticate to the pma.core server
    """
    def get_filename_from_cd(cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None
        fname = re.findall('filename=(\S+)', cd)
        if len(fname) == 0:
            return None
        return fname[0].strip(";")

    if not slideRef:
        raise ValueError("slide cannot be empty")

    if save_directory and not os.path.exists(save_directory):
        raise ValueError("The output directory does not exist {}".format(save_directory))
    
    sessionID = _pma_session_id(sessionID)
    files = get_files_for_slide(slideRef, sessionID)
    if not files:
        raise ValueError("Slide not found")
    
    mainDirectory = slideRef.rsplit('/', 1)[0]
   
    for f in files:
        relativePath = f.replace(mainDirectory, '').strip("\\").strip("/")
        pmaCoreDownloadUrl = _pma_url(sessionID) + "transfer/Download/"

        if pma._pma_debug == True:
            print("Downloading file {} for slide {}".format(relativePath, slideRef))

        params = {"sessionId": sessionID, "image": slideRef, "path": relativePath}

        with requests.get(pmaCoreDownloadUrl, params=params, stream=True) as r:
            r.raise_for_status()

            total = int(r.headers.get('content-length'))
            downloaded = 0

            if save_directory:
                filePath = os.path.join(save_directory, relativePath)

            dir = os.path.dirname(filePath)
            if not os.path.exists(dir):
                os.makedirs(dir)
            prev = -1
            with open(filePath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=10 * 1024):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        progress = downloaded / total
                        if not prev or progress - prev > 0.05 or (progress - prev > 0 and downloaded == total):
                            if pma._pma_debug == True:
                                print("{0:.0%}".format(progress))
                            prev = progress
