from pma_python import core
from sys import exit

if (not core.is_lite()):
	print("PMA.start is not running. Please start PMA.start")
	exit(1)

sessionID = core.connect()	# // no parameters needed for PMA.start

if (sessionID == None):
	print("Unable to connect to PMA.start");
else:
	print("Successfully connected to PMA.start; sessionID", sessionID)
