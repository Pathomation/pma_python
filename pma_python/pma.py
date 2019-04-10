from urllib.parse import quote
from os.path import join
import requests

__version__ = "2.0.0.66"

_pma_url_content = {}

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
	
	if not (url in _pma_url_content):
		print("Retrieving ", url)
		r = requests.get(url, headers=headers)
		_pma_url_content[url] = r
	
	return _pma_url_content[url]