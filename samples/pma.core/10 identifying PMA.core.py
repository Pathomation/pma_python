from pma_python import core
from config import config as cfg
 
# testing actual "full" PMA.core instance that may or may not be out there
print("Are you running PMA.start at ", cfg.pma_core_server , "? " + str(core.is_lite(cfg.pma_core_server)))
