from pma_python import core
from sys import exit

if (not core.is_lite()):
	print("PMA.start is not running. Please start PMA.start")
	exit(1)

sessionID = core.connect()
if (sessionID is None):
	print ("Unable to connect to PMA.start")
	exit(2)
	
print ("Successfully connected to PMA.start")
	
rootdirs = core.get_root_directories();
print("Directories found in ", rootdirs[0],":")
	
dirs = core.get_directories(rootdirs[0], sessionID)
for d in dirs:
	print(d)
