"""
Startup sequence for the Q-ETL engine: loads settings, initializes logging,
boots the headless QGIS application and registers the Processing plugin.

Kept separate from core/__init__.py so the sequence is a single, testable
function instead of import-time side effects scattered across the module.
"""
import sys
import atexit
import tracemalloc

from qgis.core import QgsApplication, Qgis

from core.logger import initialize_logger, start_logfile, get_logger
from core.misc import (
    get_config,
    validateEnvironment,
    describeEngine,
    get_postgres_connections,
    get_bin_folder,
    script_finished,
)

_state = {}


def initialize():
    """
    Runs the Q-ETL startup sequence once per process and returns
    (qgs, settings, logger). Safe to call more than once - subsequent
    calls return the already-initialized instances instead of booting
    QGIS again.
    """
    if _state:
        return _state['qgs'], _state['settings'], _state['logger']

    tracemalloc.start()

    settings = get_config()
    logger = initialize_logger(settings)
    start_logfile()

    settings['bin_path'] = get_bin_folder(settings)
    validateEnvironment(settings)
    settings['Postgres_Ponnections'] = get_postgres_connections(settings)

    QgsApplication.setPrefixPath(settings["Qgs_PrefixPath"], True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    ## Loading the Processing plugin...
    try:
        sys.path.append(settings["QGIS_Plugin_Path"])
        import processing
        from processing.core.Processing import Processing
        from processing.script.ScriptUtils import ScriptUtils
        from qgis.analysis import QgsNativeAlgorithms
        Processing.initialize()
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        logger.info('QGIS ressources loaded sucesfully')
    except Exception as e:
        logger.error('Error loading QGIS ressources')
        logger.error(e)
        logger.critical('Program terminated')
        sys.exit()

    describeEngine(
        ScriptUtils.scriptsFolders(),
        QgsApplication.processingRegistry().providerById("script").algorithms(),
        Qgis.QGIS_VERSION,
    )

    atexit.register(script_finished)

    _state['qgs'] = qgs
    _state['settings'] = settings
    _state['logger'] = logger
    return qgs, settings, logger
