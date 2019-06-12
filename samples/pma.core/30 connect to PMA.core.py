from pma_python import core
from config import config as cfg

sessionID = core.connect(cfg.pma_core_server, cfg.pma_core_user, cfg.pma_core_pass)	

if (sessionID == None):
	print("Unable to connect to PMA.core");
else:
	print("Successfully connected to PMA.core; sessionID", sessionID)
