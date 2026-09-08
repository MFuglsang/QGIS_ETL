from core.logger import get_logger
from core.misc import script_failed
from core.bootstrap import initialize

## Boots the QGIS engine (config, logging, QGIS app, Processing plugin).
## Safe to import more than once - initialize() only runs the sequence once.
qgs, settings, logger = initialize()

__all__ = ['qgs', 'settings', 'logger', 'get_logger', 'script_failed']
