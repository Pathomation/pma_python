from urllib.parse import quote
from os.path import join

__version__ = "2.0.0.46"

def _pma_join(*s):
	joinstring = ""
	for ss in s:
		if not (ss is None):
			joinstring = join(joinstring, ss)
	return joinstring.replace("\\", "/")
