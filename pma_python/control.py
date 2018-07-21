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
	"""
	Retrieve a list of currently defined training sessions in PMA.control.
	"""
	url = pma._pma_join(pmacontrolURL, "api/Sessions?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()

def get_session_ids(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve a dictionary with currently defined training sessions in PMA.control.
	The resulting dictionary use the session's identifier as the dictionary key, and 
	therefore this method is easier to quickly retrieve and represent session-related data. 
	However, this method returns less verbose data than get_sessions()
	"""
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
	
def get_case_collections(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all the data for all the defined case collections in PMA.control
	"""
	url = pma._pma_join(pmacontrolURL, "api/CaseCollections?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()
	
def get_projects(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all projects and their data in PMA.control
	"""
	url = pma._pma_join(pmacontrolURL, "api/Projects?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()
