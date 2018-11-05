import os
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

# internal module helper variables and functions
_pma_sessions = dict()
_pma_slideinfos = dict()
_pma_pmacoreliteURL = "http://localhost:54001/"
_pma_pmacoreliteSessionID = "SDK.Python"
_pma_usecachewhenretrievingtiles = True
_pma_amount_of_data_downloaded = {_pma_pmacoreliteSessionID: 0}

def _pma_session_id(sessionID = None):
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
			if (not _pma_pmacoreliteSessionID in _pma_slideinfos):
				# _pma_sessions[_pma_pmacoreliteSessionID] = _pma_pmacoreliteURL
				
				_pma_slideinfos[_pma_pmacoreliteSessionID] = dict()
			if (not  _pma_pmacoreliteSessionID in _pma_amount_of_data_downloaded):
				_pma_amount_of_data_downloaded[_pma_pmacoreliteSessionID] = 0
			return _pma_pmacoreliteSessionID
		else:
			# no stored PMA.core sessions found NOR PMA.core.lite
			return None
	
def _pma_url(sessionID = None):	
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

def _pma_is_lite(pmacoreURL = _pma_pmacoreliteURL):
	url = pma._pma_join(pmacoreURL, "api/xml/IsLite")
	try:
		contents = urlopen(url).read()
	except Exception as e:
		# this happens when NO instance of PMA.core is detected
		return None
	dom = minidom.parseString(contents)	
	return str(dom.firstChild.firstChild.nodeValue).lower() == "true"

def _pma_api_url(sessionID = None, xml = True):
	# let's get the base URL first for the specified session
	url = _pma_url(sessionID)
	if url is None:
		# sort of a hopeless situation; there is no URL to refer to
		return None
	# remember, _pma_url is guaranteed to return a URL that ends with "/"
	if (xml == True):
		return pma._pma_join(url, "api/xml/")
	else:
		return pma._pma_join(url, "api/json/")
		
def _pma_XmlToStringArray(root, limit = 0):
	els = root.getElementsByTagName("string")
	l = []
	if (limit > 0):
		for el in els[0: limit]:
			l.append(el.firstChild.nodeValue)
	else:
		for el in els:
			l.append(el.firstChild.nodeValue)
	return l
	
# end internal module helper variables and functions
	
def is_lite(pmacoreURL = _pma_pmacoreliteURL):
	"""
	See if there's a PMA.core.lite or PMA.core instance running at pmacoreURL
	"""
	return _pma_is_lite(pmacoreURL)
	
def get_version_info(pmacoreURL = _pma_pmacoreliteURL):
	"""
	Get version info from PMA.core instance running at pmacoreURL
	"""
	# purposefully DON'T use helper function _pma_api_url() here:
	# why? because GetVersionInfo can be invoked WITHOUT a valid SessionID; _pma_api_url() takes session information into account
	url = pma._pma_join(pmacoreURL, "api/xml/GetVersionInfo")
	try:
		contents = urlopen(url).read()
	except Exception as e:
		return None		
	dom = minidom.parseString(contents)	
	return (dom.firstChild.firstChild.nodeValue)

def connect(pmacoreURL = _pma_pmacoreliteURL, pmacoreUsername = "", pmacorePassword = ""):
	"""
	Attempt to connect to PMA.core instance; success results in a SessionID
	"""
	if (pmacoreURL == _pma_pmacoreliteURL):
		if is_lite():
			# no point authenticating localhost / PMA.core.lite
			return _pma_pmacoreliteSessionID
		else:
			return None
			
	# purposefully DON'T use helper function _pma_api_url() here:	
	# why? Because_pma_api_url() takes session information into account (which we don't have yet)
	url = pma._pma_join(pmacoreURL, "api/xml/authenticate?caller=SDK.Python") 
	if (pmacoreUsername != ""):
		url += "&username=" + pma._pma_q(pmacoreUsername)
	if (pmacorePassword != ""):
		url += "&password=" + pma._pma_q(pmacorePassword)
	
	try:
		contents = urlopen(url).read()
		dom = minidom.parseString(contents)
	except:
		# Something went wrong; unable to communicate with specified endpoint
		return None
		
	loginresult = dom.firstChild
	succ = loginresult.getElementsByTagName("Success")[0]
	
	if (succ.firstChild.nodeValue.lower() == "false"):
		sessionID = None
	else:
		sessionID = loginresult.getElementsByTagName("SessionId")[0]
		sessionID = sessionID.firstChild.nodeValue
		
		global _pma_sessions
		_pma_sessions[sessionID] = pmacoreURL
		global _pma_slideinfos
		_pma_slideinfos[sessionID] = dict()
		global _pma_amount_of_data_downloaded
		_pma_amount_of_data_downloaded[sessionID] = len(contents)
	
	return (sessionID)	

def disconnect(sessionID = None):
	"""
	Attempt to connect to PMA.core instance; success results in a SessionID
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

def get_root_directories(sessionID = None):
	"""
	Return an array of root-directories available to sessionID
	"""
	sessionID = _pma_session_id(sessionID)
	url = _pma_api_url(sessionID) + "GetRootDirectories?sessionID=" + pma._pma_q((sessionID))
	contents = urlopen(url).read()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(contents)
	dom = minidom.parseString(contents)
	return _pma_XmlToStringArray(dom.firstChild)

def get_directories(startDir, sessionID = None, recursive = False):
	"""
	Return an array of sub-directories available to sessionID in the startDir directory
	"""
	sessionID = _pma_session_id(sessionID)
	url = _pma_api_url(sessionID, False) + "GetDirectories?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(startDir)
	r = requests.get(url)
	json = r.json()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(json)
	if ("Code" in json):
		raise Exception("get_directories to " + startDir + " resulted in: " + json["Message"] + " (keep in mind that startDir is case sensitive!)")
	elif ("d" in json):
		dirs  = json["d"]
	else:
		dirs = json

	# handle recursion, if so desired
	if (type(recursive) == bool and recursive == True) or (type(recursive) == int and recursive > 0):
		for dir in get_directories(startDir, sessionID):
			if type(recursive) == bool:
				dirs = dirs + get_directories(dir, sessionID, recursive)	
			elif type(recursive) == int:
				dirs = dirs + get_directories(dir, sessionID, recursive - 1)
		
	return dirs

def get_first_non_empty_directory(startDir = None, sessionID = None):
	sessionID = _pma_session_id(sessionID)

	if ((startDir is None) or (startDir == "")):
		startDir = "/"
	slides = get_slides(startDir = startDir, sessionID = sessionID)
	if (len(slides) > 0):
		return startDir
	else:
		if (startDir == "/"):
			for dir in get_root_directories(sessionID = sessionID):
				nonEmtptyDir = get_first_non_empty_directory(startDir = dir, sessionID = sessionID)
				if (not (nonEmtptyDir is None)):
					return nonEmtptyDir
		else:
			for dir in get_directories(startDir, sessionID):
				nonEmtptyDir = get_first_non_empty_directory(startDir = dir, sessionID = sessionID)
				if (not (nonEmtptyDir is None)):
					return nonEmtptyDir
	return None

def get_slides(startDir, sessionID = None, recursive = False):
	"""
	Return an array of slides available to sessionID in the startDir directory
	"""
	sessionID = _pma_session_id(sessionID)
	if (startDir.startswith("/")):
		startDir = startDir[1:]		
	url = _pma_api_url(sessionID, False) + "GetFiles?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(startDir)	
	r = requests.get(url)
	json = r.json()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(json)
	if ("Code" in json):
		raise Exception("get_slides from " + startDir + " resulted in: " + json["Message"] + " (keep in mind that startDir is case sensitive!)")
	elif ("d" in json):
		slides  = json["d"]
	else:
		slides = json

	# handle recursion, if so desired
	if (type(recursive) == bool and recursive == True) or (type(recursive) == int and recursive > 0):
		for dir in get_directories(startDir, sessionID):
			if type(recursive) == bool:
				slides = slides + get_slides(dir, sessionID, recursive)	
			elif type(recursive) == int:
				slides = slides + get_slides(dir, sessionID, recursive - 1)
				
	return slides

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

def get_uid(slideRef, sessionID = None):
	"""
	Get the UID for a specific slide 
	"""
	sessionID = _pma_session_id(sessionID)
	url = _pma_api_url(sessionID) + "GetUID?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(slideRef)
	contents = urlopen(url).read()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(contents)
	dom = minidom.parseString(contents)
	return _pma_XmlToStringArray(dom)[0]
	
def get_fingerprint(slideRef, strict = False, sessionID = None):
	"""
	Get the fingerprint for a specific slide 
	"""
	sessionID = _pma_session_id(sessionID)
	url = _pma_api_url(sessionID, False) + "GetFingerprint?sessionID=" + pma._pma_q(sessionID) + "&strict=" + pma._pma_q(str(strict)) + "&pathOrUid=" + pma._pma_q(slideRef)

	r = requests.get(url)
	json = r.json()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(json)
	if ("Code" in json):
		raise Exception("get_fingerprint on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
	else:
		fingerprint = json
	return fingerprint

def who_am_i():
	"""
	Getting information about your Session (under construction)
	"""
	print ("Under construction")
	return "Under construction"
	
def sessions():
	global _pma_sessions
	return _pma_sessions

def get_tile_size(sessionID = None):
	sessionID = _pma_session_id(sessionID)
	global _pma_slideinfos
	if (len(_pma_slideinfos[sessionID]) < 1):
		dir = get_first_non_empty_directory(sessionID)
		slides = get_slides(dir, sessionID)
		info = get_slide_info(slides[0], sessionID)
	else:
		info = choice(list(_pma_slideinfos[sessionID].values()))
		
	return (int(info["TileSize"]), int(info["TileSize"]))
	
def get_slide_info(slideRef, sessionID = None):
	"""
	Return raw image information in the form of nested dictionaries
	"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
		
	global _pma_slideinfos

	if (not (slideRef in _pma_slideinfos[sessionID])):
		url = _pma_api_url(sessionID, False) + "GetImageInfo?SessionID=" + pma._pma_q(sessionID) +  "&pathOrUid=" + pma._pma_q(slideRef)
		r = requests.get(url)
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("ImageInfo to " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		elif ("d" in json):
			_pma_slideinfos[sessionID][slideRef] = json["d"]
		else:
			_pma_slideinfos[sessionID][slideRef] = json
			
	return _pma_slideinfos[sessionID][slideRef]

def get_max_zoomlevel(slideRef, sessionID = None):
	"""
	Determine the maximum zoomlevel that still represents an optical magnification
	"""
	info = get_slide_info(slideRef, sessionID)
	if (info == None):
		print("Unable to get information for", slideRef, " from ", sessionID)
		return 0
	else:
		if ("MaxZoomLevel" in info): 
			try:
				return int(info["MaxZoomLevel"])
			except:
				print("Something went wrong consulting the MaxZoomLevel key in info{} dictionary; value =", info["MaxZoomLevel"])
				return 0
		else:
			try:
				return int(info["NumberOfZoomLevels"])
			except:
				print("Something went wrong consulting the NumberOfZoomLevels key in info{} dictionary; value =", info["NumberOfZoomLevels"])
				return 0

def get_zoomlevels_list(slideRef, sessionID = None, min_number_of_tiles = 0):
	"""
	Obtain a list with all zoomlevels, starting with 0 and up to and including max_zoomlevel
	Use min_number_of_tiles argument to specify that you're only interested in zoomlevels that include at lease a given number of tiles
	"""
	return sorted(list(get_zoomlevels_dict(slideRef, sessionID, min_number_of_tiles).keys()))

def get_zoomlevels_dict(slideRef, sessionID = None, min_number_of_tiles = 0):
	"""
	Obtain a dictionary with the number of tiles per zoomlevel.
	Information is returned as (x, y, n) tupels per zoomlevel, with 
		x = number of horizontal tiles, 
		y = number of vertical tiles, 
		n = total number of tiles at specified zoomlevel (x * y)
	Use min_number_of_tiles argument to specify that you're only interested in zoomlevels that include at lease a given number of tiles
	"""
	zoomlevels = list(range(0, get_max_zoomlevel(slideRef, sessionID) + 1))
	dimensions = [ get_number_of_tiles(slideRef, z, sessionID) for z in zoomlevels if get_number_of_tiles(slideRef, z, sessionID)[2] > min_number_of_tiles]
	d = dict(zip(zoomlevels[-len(dimensions):], dimensions))
	
	
	return d
	
def get_pixels_per_micrometer(slideRef, zoomlevel = None, sessionID = None):
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
		factor = 2 ** (zoomlevel - maxZoomLevel)
		return (float(xppm) / factor, float(yppm) / factor)		
	
def get_pixel_dimensions(slideRef, zoomlevel = None, sessionID = None):
	"""Get the total dimensions of a slide image at a given zoomlevel"""
	maxZoomLevel = get_max_zoomlevel(slideRef, sessionID)
	info = get_slide_info(slideRef, sessionID)
	if (zoomlevel is None or zoomlevel == maxZoomLevel):
		return (int(info["Width"]), int(info["Height"]))
	else:
		factor = 2 ** (zoomlevel - maxZoomLevel)
		return (int(info["Width"]) * factor, int(info["Height"]) * factor)

def get_number_of_tiles(slideRef, zoomlevel = None, sessionID = None):
	"""Determine the number of tiles needed to reconstitute a slide at a given zoomlevel"""
	pixels = get_pixel_dimensions(slideRef, zoomlevel, sessionID)
	sz = get_tile_size(sessionID)
	xtiles = int(ceil(pixels[0] / sz[0]))
	ytiles = int(ceil(pixels[1] / sz[0]))
	ntiles = xtiles * ytiles
	return (xtiles, ytiles, ntiles)
	
def get_physical_dimensions(slideRef, sessionID = None):
	"""Determine the physical dimensions of the sample represented by the slide.
	This is independent of the zoomlevel: the physical properties don't change because the magnification changes"""
	ppmData = get_pixels_per_micrometer(slideRef, sessionID)
	pixelSz = get_pixel_dimensions(slideRef, sessionID)
	return (pixelSz[0] * ppmData[0], pixelSz[1] * ppmData[1])
			
def get_number_of_channels(slideRef, sessionID = None):
	"""Number of fluorescent channels for a slide (when slide is brightfield, return is always 1)"""
	info = get_slide_info(slideRef, sessionID)
	channels = info["TimeFrames"][0]["Layers"][0]["Channels"]
	return len(channels)

def get_number_of_layers(slideRef, sessionID = None):
	"""Number of (z-stacked) layers for a slide"""
	info = get_slide_info(slideRef, sessionID)
	layers = info["TimeFrames"][0]["Layers"]
	return len(layers)

def get_number_of_z_stack_layers(slideRef, sessionID = None):
 	return get_number_of_layers(slideRef, sessionID)

def is_fluorescent(slideRef, sessionID = None):
	"""Determine whether a slide is a fluorescent image or not"""
	return get_number_of_channels(slideRef, sessionID) > 1

def is_multi_layer(slideRef, sessionID = None):
	"""Determine whether a slide contains multiple (stacked) layers or not"""
	return get_number_of_layers(slideRef, sessionID) > 1

def is_z_stack(slideRef, sessionID = None):
	"""Determine whether a slide is a z-stack or not"""
	return is_multi_layer(slideRef, sessionID)
	
def get_magnification(slideRef, zoomlevel = None, exact = False, sessionID = None):
	"""Get the magnification represented at a certain zoomlevel"""
	ppm = get_pixels_per_micrometer(slideRef, zoomlevel, sessionID)[0]
	if (ppm > 0):
		if (exact == True):
			return round(40 / (ppm / 0.25))
		else:
			return round(40 / round(ppm / 0.25))
	else:
		return 0

def get_barcode_url(slideRef, sessionID = None):
	"""Get the URL that points to the barcode (alias for "label") for a slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = (_pma_url(sessionID) + "barcode"
		+ "?SessionID=" + pma._pma_q(sessionID)
		+ "&pathOrUid=" + pma._pma_q(slideRef))
	return url

def get_barcode_image(slideRef, sessionID = None):
	"""Get the barcode (alias for "label") image for a slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	r = requests.get(get_barcode_url(slideRef, sessionID))
	img = Image.open(BytesIO(r.content))
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(r.content)
	return img

def get_barcode_text(slideRef, sessionID = None):
	"""Get the text encoded by the barcode (if there IS a barcode on the slide to begin with)"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = _pma_api_url(sessionID, False) + "GetBarcodeText?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)
	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_barcode_text on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		else:
			barcode = json
	else:
		barcode = ""
	return barcode

	
def get_label_url(slideRef, sessionID = None):
	"""Get the URL that points to the label for a slide"""
	return get_barcode_url(slideRef, sessionID)
	
def get_label_image(slideRef, sessionID = None):
	"""Get the label image for a slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	r = requests.get(get_label_url(slideRef, sessionID))
	img = Image.open(BytesIO(r.content))
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(r.content)
	return img
		
def get_thumbnail_url(slideRef, sessionID = None):
	"""Get the URL that points to the thumbnail for a slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = (_pma_url(sessionID) + "thumbnail"
		+ "?SessionID=" + pma._pma_q(sessionID)
		+ "&pathOrUid=" + pma._pma_q(slideRef))
	return url
	
def get_thumbnail_image(slideRef, sessionID = None):
	"""Get the thumbnail image for a slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = get_thumbnail_url(slideRef, sessionID)
	r = requests.get(url)
	img = Image.open(BytesIO(r.content))
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(r.content)
	return img

def get_tile(slideRef, x = 0, y = 0, zoomlevel = None, zstack = 0, sessionID = None, format = "jpg", quality = 100): 
	"""
	Get a single tile at position (x, y)
	Format can be 'jpg' or 'png'
	Quality is an integer value and varies from 0 (as much compression as possible; not recommended) to 100 (100%, no compression)
	"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	if (zoomlevel is None):
		zoomlevel = 0   # get_max_zoomlevel(slideRef, sessionID)

	url = _pma_url(sessionID)
	if url is None:
		raise Exception("Unable to determine the PMA.core instance belonging to " + str(sessionID))

	url += ("tile"
		+ "?SessionID=" + pma._pma_q(sessionID)
		+ "&channels=" + pma._pma_q("0")
		+ "&timeframe=" + pma._pma_q("0")
		+ "&layer=" + str(int(round(zstack)))
		+ "&pathOrUid=" + pma._pma_q(slideRef)
		+ "&x=" + str(int(round(x)))
		+ "&y=" + str(int(round(y)))
		+ "&z=" + str(int(round(zoomlevel)))
		+ "&format=" + pma._pma_q(format)
		+ "&quality=" + pma._pma_q(quality)
		+ "&cache=" + str(_pma_usecachewhenretrievingtiles).lower())

	r = requests.get(url)
	img = Image.open(BytesIO(r.content))
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(r.content)
	return img

def get_submitted_forms(slideRef, sessionID = None):
	"""Find out what forms where submitted for a specific slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = _pma_api_url(sessionID, False) + "GetFormSubmissions?sessionID=" + pma._pma_q(sessionID) + "&pathOrUids=" + pma._pma_q(slideRef)
	all_forms = get_available_forms(slideRef, sessionID)
	print(url)
	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
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
	
def get_submitted_form_data(slideRef, sessionID = None):
	"""Get all submitted form data associated with a specific slide"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	url = _pma_api_url(sessionID, False) + "GetFormSubmissions?sessionID=" + pma._pma_q(sessionID) + "&pathOrUids=" + pma._pma_q(slideRef)
	print(url)
	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		else:
			data = json
			# should probably do some post-processing here, but unsure what that would actually be??
	else:
		data = ""
	return data
	
def get_available_forms(slideRef = None, sessionID = None):
	"""
	See what forms are available to fill out, either system-wide (leave slideref to None), or for a particular slide
	"""
	sessionID = _pma_session_id(sessionID)
	if (not slideRef == None):
		if (slideRef.startswith("/")):
			slideRef = slideRef[1:]
		dir = os.path.split(slideRef)[0]
		url = _pma_api_url(sessionID, False) + "GetForms?sessionID=" + pma._pma_q(sessionID) + "&path=" + pma._pma_q(dir)
	else:
		url = _pma_api_url(sessionID, False) + "GetForms?sessionID=" + pma._pma_q(sessionID)
	
	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		else:
			forms_json = json
			forms = {}
			for entry in forms_json:
				forms[entry["Key"]] = entry["Value"]
	else:
		forms = ""
	return forms

def prepare_form_dictionary(formID, sessionID = None):
	"""Prepare a form-dictionary that can be used later on to submit new form data for a slide"""
	if (formID == None):
		return None
	sessionID = _pma_session_id(sessionID)
	url = _pma_api_url(sessionID, False) + "GetFormDefinitions?sessionID=" + pma._pma_q(sessionID)
	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_available_forms on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		else:
			forms_json = json
			form_def = {}
			for form in forms_json:
				if ( (form["FormID"] == formID) or (form["FormName"] == formID) ):
					for field in form["FormFields"]:
						form_def[field["Label"]] = None
	else:
		form_def = ""
	return form_def
	
	
def submit_form_data(slideRef, formID, formDict, sessionID = None):
	"""Not implemented yet"""
	sessionID = _pma_session_id(sessionID)
	if (not slideRef == None):
		if (slideRef.startswith("/")):
			slideRef = slideRef[1:]
	return None
	
def get_annotations(slideRef, sessionID = None):
	"""
	Retrieve the annotations for slide slideRef
	"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]
	dir = os.path.split(slideRef)[0]
	url = _pma_api_url(sessionID, False) + "GetAnnotations?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)

	r = requests.get(url)
	if ( (not (r.text is None)) and (len(r.text) > 0) ):
		json = r.json()
		global _pma_amount_of_data_downloaded 
		_pma_amount_of_data_downloaded[sessionID] += len(json)
		if ("Code" in json):
			raise Exception("get_annotations() on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
		else:
			annotations = json
	else:
		annotations = ""
	return annotations
	
def get_tiles(slideRef, fromX = 0, fromY = 0, toX = None, toY = None, zoomlevel = None, zstack = 0, sessionID = None, format = "jpg", quality = 100):
	"""
	Get all tiles with a (fromX, fromY, toX, toY) rectangle. Navigate left to right, top to bottom
	Format can be 'jpg' or 'png'
	Quality is an integer value and varies from 0 (as much compression as possible; not recommended) to 100 (100%, no compression)
	"""
	sessionID = _pma_session_id(sessionID)
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]

	if (zoomlevel is None):
		zoomlevel = 0   # get_max_zoomlevel(slideRef, sessionID)
	if (toX is None):
		toX = get_number_of_tiles(slideRef, zoomlevel, sessionID)[0]
	if (toY is None):
		toY = get_number_of_tiles(slideRef, zoomlevel, sessionID)[1]
	for x in range(fromX, toX):
		for y in range(fromY, toY):
			yield get_tile(slideRef = slideRef, x = x, y = y, zstack = zstack, zoomlevel = zoomlevel, sessionID = sessionID, format = format, quality = quality)
			
def show_slide(slideRef, sessionID = None):
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
			url += ("viewer/index.htm"
			+ "?sessionID=" + pma._pma_q(sessionID)
			+ "^&pathOrUid=" + pma._pma_q(slideRef))    # note the ^& to escape a regular &
	os.system(os_cmd+url)
	
def enumerate_files_for_slide(slideRef, sessionID = None):
	"""Obtain all files actually associated with a specific slide
	This is most relevant with slides that are defined by multiple files, like MRXS or VSI"""
	sessionID = _pma_session_id(sessionID)
	
	if (slideRef.startswith("/")):
		slideRef = slideRef[1:]		
	url = _pma_api_url(sessionID, False) + "EnumerateAllFilesForSlide?sessionID=" + pma._pma_q(sessionID) + "&pathOrUid=" + pma._pma_q(slideRef)	
	r = requests.get(url)
	json = r.json()
	global _pma_amount_of_data_downloaded 
	_pma_amount_of_data_downloaded[sessionID] += len(json)
	if ("Code" in json):
		raise Exception("enumerate_files_for_slide on  " + slideRef + " resulted in: " + json["Message"] + " (keep in mind that slideRef is case sensitive!)")
	elif ("d" in json):
		files  = json["d"]
	else:
		files = json
	return files
	