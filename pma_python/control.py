import os
import requests
from pma_python import core, pma

__version__ = pma.__version__

_pma_casecollections_json = {}
_pma_projects_json = {} 
_pma_session_json = {}

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
	global _pma_casecollections_json
	
	url = pma._pma_join(pmacontrolURL, "api/CaseCollections?sessionID=" + pma._pma_q(pmacoreSessionID))
	if not (url in _pma_casecollections_json):
		print (url)
		try:
			headers = {'Accept': 'application/json'}
			r = requests.get(url, headers=headers)
			_pma_casecollections_json[url] = r.json()
		except Exception as e:
			return None		

	return _pma_casecollections_json[url]

def get_case_collection_titles(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve case collections (possibly filtered by project ID), titles only
	"""
	try:
		return list(get_case_collection_titles_dict(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID).values())
	except Exception as e:
		return None		
	
def get_case_collection_titles_dict(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve case collections (possibly filtered by project ID), return a dictionary of case collection IDs and titles
	"""
	dct = {}
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		if pmacontrolProjectID == None:
			dct[coll["Id"]] = coll["Title"]
		elif pmacontrolProjectID == coll["ModuleId"]:
			dct[coll["Id"]] = coll["Title"]

	return dct

def get_case_collection(pmacontrolURL, pmacontrolCaseCollectionID, pmacoreSessionID):
	"""
	Retrieve case collection details
	"""
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		if coll["Id"] == pmacontrolCaseCollectionID:
			return coll

	return None
	
def _pma_format_project_embedded_sessions_properly(original_project_sessions):
	"""
	Helper method to convert a list of sessions with default arguments into a summarized dictionary
	"""
	dct = {}
	for prj_sess in original_project_sessions:
		dct[prj_sess["Id"]] = prj_sess["Title"]

	return dct
	
def _pma_get_projects(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all projects and their data in PMA.control 
	(RAW JSON data; not suited for human consumption)
	"""
	global _pma_projects_json
	
	url = pma._pma_join(pmacontrolURL, "api/Projects?sessionID=" + pma._pma_q(pmacoreSessionID))
	if not (url in _pma_projects_json):
		print (url)
		try:
			headers = {'Accept': 'application/json'}
			r = requests.get(url, headers=headers)
		except Exception as e:
			return None		
		_pma_projects_json[url] = r.json()
		
	return _pma_projects_json[url]

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

def get_project_by_case_id(pmacontrolURL, pmacontrolCaseID, pmacoreSessionID):
	"""
	Retrieve case collection based on the case ID
	"""
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		for case in coll["Cases"]:
			if case["Id"] == pmacontrolCaseID:
				return get_project(pmacontrolURL, coll["ModuleId"], pmacoreSessionID)

	return None
	
def get_project_by_case_collection_id(pmacontrolURL, pmacontrolCaseCollectionID, pmacoreSessionID):
	"""
	Retrieve case collection based on the case ID
	"""
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		if coll["Id"] == pmacontrolCaseCollectionID:
			return get_project(pmacontrolURL, coll["ModuleId"], pmacoreSessionID)

	return None

def search_project(pmacontrolURL, titleSubstring, pmacoreSessionID):
	"""
	Return the first project that has titleSubstring as part of its string; search is case insensitive
	"""
	all_projects = _pma_get_projects(pmacontrolURL, pmacoreSessionID)

	for prj in all_projects:
		if titleSubstring.lower() in prj['Title'].lower():
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