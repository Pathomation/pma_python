from pma_python import core
from sys import exit

if (not core.is_lite()):
	print("PMA.start is not running. Please start PMA.start")
	exit(1)

sessionID = core.connect()
if (sessionID is None):
	print ("Unable to connect to PMA.start")
	exit(2)

dir = core.get_first_non_empty_directory()

print("Looking for slides in " + dir)
print()

for slide in core.get_slides(dir):
	print (slide," - ", core.get_uid(slide))
