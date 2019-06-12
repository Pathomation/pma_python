from pma_python import core
from config import config as cfg


# assuming we have PMA.core running; what's the version number?
print("Investigating", cfg.pma_core_server)
print("You are running PMA.start version", core.get_version_info(cfg.pma_core_server))
