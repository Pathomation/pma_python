from urllib.parse import quote
from os.path import join
import requests

__version__ = "2.0.0.84"

_pma_url_content = {}
_pma_debug = False

def _pma_join(*s):
	joinstring = ""
	for ss in s:
		if not (ss is None):
			joinstring = join(joinstring, ss)
	return joinstring.replace("\\", "/")

def _pma_q(arg):
	if (arg is None):
		return ''
	else:
		return quote(str(arg), safe='')
	
def _pma_http_get(url, headers):
	global _pma_url_content
	global _pma_debug
	
	if not (url in _pma_url_content):
		if _pma_debug == True:
			print("Retrieving ", url)
		r = requests.get(url, headers=headers)
		_pma_url_content[url] = r
	
	return _pma_url_content[url]
	
def _pma_clear_url_cache():
	global _pma_url_content
	_pma_url_content = {}