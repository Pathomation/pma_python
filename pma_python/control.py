import os
import requests
from urllib import request, parse
from pma_python import core, pma

__version__ = pma.__version__

pma_session_role_supervisor = 1
pma_session_role_trainee = 2
pma_session_role_observer = 3

pma_interaction_mode_locked = 0
pma_interaction_mode_test_active = 1
pma_interaction_mode_review = 2
pma_interaction_mode_consensus_view = 3
pma_interaction_mode_browse = 4
pma_interaction_mode_board = 5
pma_interaction_mode_consensus_score_edit = 6
pma_interaction_mode_self_review = 7
pma_interaction_mode_self_test = 8
pma_interaction_mode_hidden = 9
pma_interaction_mode_clinical_information_edit = 10

def get_version_info(pmacontrolURL):
	"""
	Get version info from PMA.control instance running at pmacontrolURL
	"""
	# why? because GetVersionInfo can be invoked WITHOUT a valid SessionID; _pma_api_url() takes session information into account
	url = pma._pma_join(pmacontrolURL, "api/version")
	try:
		headers = {'Accept': 'application/json'}
		# r = requests.get(url, headers=headers)
		r = pma._pma_http_get(url, headers)
	except Exception as e:
		print(e)
		return None		
	return r.json()

def _pma_get_sessions(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve a list of currently defined training sessions in PMA.control.
	"""
	url = pma._pma_join(pmacontrolURL, "api/Sessions?sessionID=" + pma._pma_q(pmacoreSessionID))
	try:
		headers = {'Accept': 'application/json'}
		# r = requests.get(url, headers=headers)
		r = pma._pma_http_get(url, headers)
	except Exception as e:
		print(e)
		return None		
	return r.json()

def _pma_format_session_properly(sess):
	"""
	Helper method to convert a JSON representation of a PMA.control training session to a proper Python-esque structure
	"""
	sess_data = {
		"Id": sess["Id"],
		"Title": sess["Title"],
		"LogoPath": sess["LogoPath"],
		"StartsOn": sess["StartsOn"],
		"EndsOn": sess["EndsOn"],
		"ProjectId": sess["ProjectId"],
		"State": sess["State"],
		"CaseCollections": {},
		"NumberOfParticipants": len(sess["Participants"])
	}
	for coll in sess["CaseCollections"]:
		sess_data["CaseCollections"][coll["CaseCollectionId"]] = { "Title": coll["Title"], "Url": coll["Url"] }

	return sess_data

def get_sessions(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve a dictionary with currently defined training sessions in PMA.control.
	The resulting dictionary use the session's identifier as the dictionary key, and 
	therefore this method is easier to quickly retrieve and represent session-related data. 
	However, this method returns less verbose data than get_sessions()
	"""
	full_sessions = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)
	new_session_dict = {}
	for sess in full_sessions:
		if (pmacontrolProjectID is None) or (pmacontrolProjectID == sess["ProjectId"]):				
			new_session_dict[sess["Id"]] = _pma_format_session_properly(sess)
	return new_session_dict

def get_sessions_for_participant(pmacontrolURL, pmacoreUsername, pmacoreSessionID):
	full_sessions = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)
	new_session_dict = {}
	for sess in full_sessions:
		for part in sess["Participants"]:
			if (part["User"].lower() == pmacoreUsername.lower()):
				s = _pma_format_session_properly(sess)
				s["Role"] = part["Role"]
				new_session_dict[sess["Id"]] = s

	return new_session_dict

def get_session_participants(pmacontrolURL, pmacontrolSessionID, pmacoreSessionID):
	"""
	Extract the participants in a particular session
	"""
	full_sessions = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)
	user_dict = {}
	for sess in full_sessions:
		if sess["Id"] == pmacontrolSessionID:
			for part in sess["Participants"]:
				user_dict[part["User"]] = part["Role"]
			return user_dict

	return None

def is_participant_in_session(pmacontrolURL, pmacoreUsername, pmacontrolSessionID, pmacoreSessionID):
	"""
	Check to see if a specific user participates in a specific session
	"""
	all_parts = get_session_participants(pmacontrolURL, pmacontrolSessionID, pmacoreSessionID)
	return pmacoreUsername in all_parts

def get_session_url(pmacontrolURL, pmacontrolSessionID, pmacontrolCase, pmacoreSessionID):
	if pmacontrolCase == None:
		return pma._pma_join(pmacontrolURL, "training/training/") + pmacontrolSessionID + "?SessionID=" + pmacoreSessionID
	elif str(pmacontrolCase.isnumeric()):
		return pma._pma_join(pmacontrolURL, "training/training/") + pmacontrolSessionID + "?SessionID=" + pmacoreSessionID
	else:
		return pma._pma_join(pmacontrolURL, "training/training/") + pmacontrolSessionID + "?SessionID=" + pmacoreSessionID

def get_all_participants(pmacontrolURL, pmacoreSessionID):
	"""
	Get a list of all participants registered across all sessions, include the Role they play
	"""
	full_sessions = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)
	user_dict = {}
	for sess in full_sessions:
		s = _pma_format_session_properly(sess)
		for part in sess["Participants"]:
			if not (part["User"] in user_dict):
				user_dict[part["User"]] = {}
			user_dict[part["User"]][sess["Id"]] = s
			user_dict[part["User"]][sess["Id"]]["Role"] = part["Role"]

	return user_dict

def register_participant_for_session(pmacontrolURL, pmacoreUsername, pmacontrolSessionID, pmacontrolRole, pmacoreSessionID):
	"""
	Registers a particpant for a given session
	"""
	if is_participant_in_session(pmacontrolURL, pmacoreUsername, pmacontrolSessionID, pmacoreSessionID):
		raise NameError ("PMA.core user " + pmacoreUsername + " is ALREADY registered in PMA.control training session " + str(pmacontrolSessionID))
	url = pma._pma_join(pmacontrolURL, "api/Sessions/") + str(pmacontrolSessionID) + "/Participants?SessionID=" + pmacoreSessionID
	data = { "UserName": pmacoreUsername, "Role": pmacontrolRole}   # default interaction mode = Locked
	data = parse.urlencode(data).encode()
	req =  request.Request(url=url, data=data) # this makes the method "POST"
	resp = request.urlopen(req)
	pma._pma_clear_url_cache()
	return resp
	
def set_participant_interactionmode(pmacontrolURL, pmacoreUsername, pmacontrolSessionID, pmacontrolCaseCollectionID, pmacontrolInteractionMode, pmacoreSessionID):
	"""
	Assign an interaction mode to a particpant for a given Case Collection with in a session
	"""
	if not is_participant_in_session(pmacontrolURL, pmacoreUsername, pmacontrolSessionID, pmacoreSessionID):
		raise NameError ("PMA.core user " + pmacoreUsername + " is NOT registered in PMA.control training session " + str(pmacontrolSessionID))
	url = pma._pma_join(pmacontrolURL, "api/Sessions/") + str(pmacontrolSessionID) + "/InteractionMode?SessionID=" + pmacoreSessionID
	data = { "UserName": pmacoreUsername, "CaseCollectionId": pmacontrolCaseCollectionID, "InteractionMode": pmacontrolInteractionMode }   
	data = parse.urlencode(data).encode()
	req =  request.Request(url=url, data=data) # this makes the method "POST"
	resp = request.urlopen(req)
	pma._pma_clear_url_cache()
	return resp
	
def get_session_titles(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve sessions (possibly filtered by project ID), titles only
	"""
	try:
		return list(get_session_titles_dict(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID).values())
	except Exception as e:
		print(e)
		return None		
	
def get_session_titles_dict(pmacontrolURL, pmacontrolProjectID, pmacoreSessionID):
	"""
	Retrieve (training) sessions (possibly filtered by project ID), return a dictionary of session IDs and titles
	"""
	dct = {}
	all = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)
	for sess in all:
		if pmacontrolProjectID == None:
			dct[sess["Id"]] = sess["Title"]
		elif pmacontrolProjectID == sess["ProjectId"]:
			dct[sess["Id"]] = sess["Title"]

	return dct

	
def search_session(pmacontrolURL, titleSubstring, pmacoreSessionID):
	"""
	Return the first (training) session that has titleSubstring as part of its string; search is case insensitive
	"""
	all = _pma_get_sessions(pmacontrolURL, pmacoreSessionID)

	for el in all:
		if titleSubstring.lower() in el['Title'].lower():
			# summarize session-related information so that it makes sense
			return _pma_format_session_properly(el)

	return None
	
def _pma_get_case_collections(pmacontrolURL, pmacoreSessionID):
	"""
	Retrieve all the data for all the defined case collections in PMA.control
	(RAW JSON data; not suited for human consumption)
	"""
	global _pma_casecollections_json
	
	url = pma._pma_join(pmacontrolURL, "api/CaseCollections?sessionID=" + pma._pma_q(pmacoreSessionID))
	try:
		headers = {'Accept': 'application/json'}
		# r = requests.get(url, headers=headers)
		r = pma._pma_http_get(url, headers)
		return r.json()
	except Exception as e:
		return None		

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
		elif pmacontrolProjectID == coll["ProjectId"]:
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

def get_cases_for_collection(pmacontrolURL, pmacontrolCaseCollectionID, pmacoreSessionID):
	"""
	Retrieve cases for a specific collection
	"""
	return get_case_collection(pmacontrolURL, pmacontrolCaseCollectionID, pmacoreSessionID)["Cases"]

def search_collection(pmacontrolURL, titleSubstring, pmacoreSessionID):
	"""
	Return the first collection that has titleSubstring as part of its string; search is case insensitive
	"""
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		if titleSubstring.lower() in coll['Title'].lower():
			# summary session-related information so that it makes sense
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
	print (url)
	try:
		headers = {'Accept': 'application/json'}
		# r = requests.get(url, headers=headers)
		r = pma._pma_http_get(url, headers)		
		return r.json()
	except Exception as e:
		return None		

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
		print(e)
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
				if col['ProjectId'] == prj['Id']:
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
				return get_project(pmacontrolURL, coll["ProjectId"], pmacoreSessionID)

	return None
	
def get_project_by_case_collection_id(pmacontrolURL, pmacontrolCaseCollectionID, pmacoreSessionID):
	"""
	Retrieve case collection based on the case ID
	"""
	all_colls = _pma_get_case_collections(pmacontrolURL, pmacoreSessionID)
	for coll in all_colls:
		if coll["Id"] == pmacontrolCaseCollectionID:
			return get_project(pmacontrolURL, coll["ProjectId"], pmacoreSessionID)

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
				if col['ProjectId'] == prj['Id']:
					prj['CaseCollections'][col['Id']] = col['Title']
					
			return prj

	return None