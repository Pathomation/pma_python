import os
from pma_python import core, pma
from math import ceil
from PIL import Image
from random import choice
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
from xml.dom import minidom

import requests

__version__ = pma.__version__

def set_debug_flag(flag):
	"""
	Determine whether pma_python runs in debugging mode or not.
	When in debugging mode (flag = true), extra output is produced when certain conditions in the code are not met
	"""
	pma._pma_set_debug_flag(flag)
	
def _pma_admin_url(sessionID = None):
	# let's get the base URL first for the specified session
	url = core._pma_url(sessionID)
	if url is None:
		# sort of a hopeless situation; there is no URL to refer to
		return None
	# remember, _pma_url is guaranteed to return a URL that ends with "/"
	return pma._pma_join(url, "admin/json/")

def _pma_check_for_pma_start(method = "", url = None, session = None):
	if (core._pma_pmacoreliteSessionID == session):
		raise Exception("PMA.start doesn't support", method);
	elif (url == core._pma_pmacoreliteURL):
		if core.is_lite():
			raise ValueError ("PMA.core.lite found running, but doesn't support an administrative back-end")
		else:
			raise ValueError ("PMA.core.lite not found, and besides; it doesn't support an administrative back-end anyway")

def admin_connect(pmacoreURL, pmacoreAdmUsername, pmacoreAdmPassword):
	"""
	Attempt to connect to PMA.core instance; success results in a SessionID
	only success if the user has administrative status
	"""
	_pma_check_for_pma_start("admin_connect", pmacoreURL)
	
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
		core._pma_usernames[admSessionID] = pmacoreAdmUsername

		if not (admSessionID in core._pma_slideinfos):
			core._pma_slideinfos[admSessionID] = dict()
		core._pma_amount_of_data_downloaded[admSessionID] = len(loginresult)
	
	return (admSessionID)

def admin_disconnect(admSessionID = None):
	"""
	Attempt to disconnect from PMA.core instance; True if valid admSessionID was indeed disconnected
	"""
	return core.disconnect(admSessionID)

def add_user(admSessionID, login, firstName, lastName, email, pwd, canAnnotate = False, isAdmin = False, isSuspended = False):
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
	print(url)
	createUserReponse = requests.post(url, json=createUserParams)
	return createUserReponse.text
	
def create_amazons3_mounting_point(accessKey, secretKey, path, instanceId, chunkSize = 1048576, serviceUrl = None): 
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
	
def	create_root_directory(admSessionID, alias, amazonS3MountingPoints = None, fileSystemMountingPoints = None, description = "Root dir created through pma_python", isPublic = False, isOffline = False):
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
