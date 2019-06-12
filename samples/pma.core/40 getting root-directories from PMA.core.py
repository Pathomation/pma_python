from pma_python import core
from sys import exit
from config import config as cfg

sessionID = core.connect(cfg.pma_core_server, cfg.pma_core_user, cfg.pma_core_pass)	

if (sessionID == None):
	print("Unable to connect to PMA.core");
	exit(1)
else:
	print("Successfully connected to PMA.core; sessionID", sessionID)
	
print("You have the following root-directories on your system: ")
rootdirs = core.get_root_directories(sessionID)
for rd in rootdirs:
	print(rd)
