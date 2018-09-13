from pma_python import core
from sys import exit

if (not core.is_lite()):
	print("PMA.start is not running. Please start PMA.start")
	exit(1)
	
# assuming we have PMA.start running; what's the version number?
print("You are running PMA.start version " + core.get_version_info())
