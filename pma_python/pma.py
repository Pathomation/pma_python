from urllib.parse import quote
from os.path import join

__version__ = "2.0.0.50"

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
	
