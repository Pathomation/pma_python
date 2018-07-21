import os
import requests
from pma_python import core, pma

__version__ = pma.__version__

def get_version_info(pmacontrolURL):
	"""
	Get version info from PMA.control instance running at pmacontrolURL
	"""
	# why? because GetVersionInfo can be invoked WITHOUT a valid SessionID; _pma_api_url() takes session information into account
	url = pma._pma_join(pmacontrolURL, "api/version")
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()

def get_sessions(pmacontrolURL, pmacoreSessionID):
	url = pma._pma_join(pmacontrolURL, "api/Sessions?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()

def get_session_ids(pmacontrolURL, pmacoreSessionID):
	full_sessions = get_sessions(pmacontrolURL, pmacoreSessionID)
	new_session_dict = {}
	for sess in full_sessions:
		sess_data = {
			"LogoPath": sess["LogoPath"],
			"StartsOn": sess["StartsOn"],
			"EndsOn": sess["EndsOn"],
			"ModuleId": sess["ModuleId"],
			"State": sess["State"]
		}
		new_session_dict[sess["Id"]] = sess_data
	return new_session_dict
	
def get_session_participants(pmacontrolURL, pmacoreSessionID, session):
	return None
	
def get_case_collections(pmacontrolURL, pmacoreSessionID):
	url = pma._pma_join(pmacontrolURL, "api/CaseCollections?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()
	
def get_projects(pmacontrolURL, pmacoreSessionID):
	url = pma._pma_join(pmacontrolURL, "api/Projects?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()
