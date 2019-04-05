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
	
def _pma_get_case_collections(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all the data for all the defined case collections in PMA.control
	(RAW JSON data; not suited for human consumption)
	"""
	url = pma._pma_join(pmacontrolURL, "api/CaseCollections?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()

def _pma_format_project_embedded_sessions_properly(original_project_sessions):
	"""
	Helper method to convert a list of sessions with default arguments into a summarized dictionary
	"""
	print(original_project_sessions)
	dct = {}
	for prj_sess in original_project_sessions:
		dct[prj_sess["Id"]] = prj_sess["Title"]

	return dct
	
def _pma_get_projects(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all projects and their data in PMA.control 
	(RAW JSON data; not suited for human consumption)
	"""
	url = pma._pma_join(pmacontrolURL, "api/Projects?sessionID=" + pma._pma_q(pmacoreSessionID))
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		r = requests.get(url, headers=headers)
	except Exception as e:
		return None		
	return r.json()


def get_project_titles(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve projects, return ONLY the titles
	"""
	try:
		return list(get_project_titles_dict(pmacontrolURL, pmacoreSessionID).values())
	except Exception as e:
		return None		

def get_project_titles_dict(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve projects, return a dictionary of project-IDs and titles
	"""
	dct = {}
	all_projects = _pma_get_projects(pmacontrolURL, pmacoreSessionID)
	try:
		for prj in all_projects:
			dct[prj['Id']] = prj['Title']
	except Exception as e:
		return None		
		
	return dct

def get_project(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve project details
	"""
	all_projects = _pma_get_projects(pmacontrolURL, pmacoreSessionID)
	for prj in all_projects:
		if prj['Id'] == pmacontrolProjectID:
			# summary session-related information so that it makes sense
			prj['Sessions'] = _pma_format_project_embedded_sessions_properly(prj['Sessions'])
			
			# now integrate case collection information
			colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
			prj['CaseCollections'] = {}
			for col in colls:
				if col['ModuleId'] == prj['Id']:
					prj['CaseCollections'][col['Id']] = col['Title']
					
			return prj
		
	return None
