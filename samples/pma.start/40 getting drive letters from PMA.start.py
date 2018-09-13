from pma_python import core
from sys import exit

if (not core.is_lite()):
	print("PMA.start is not running. Please start PMA.start")
	exit(1)

sessionID = core.connect()
if (sessionID is None):
	print ("Unable to connect to PMA.start")
	exit(2)
	
print("You have the following drives in your system: ")
rootdirs = core.get_root_directories()
for rd in rootdirs:
	print(rd)
