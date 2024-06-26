from core.logger import *
import sys
import platform,socket,re,uuid,json
import pip._internal as pip
from sys import argv
import os.path as path
import json
from PyQt5.QtCore import QSettings

def validateEnvironment(settings):
    logger = get_logger()
    logger.info('Validating Environment and settings')
    ## validating QGIS ressources
    isExist = os.path.exists(settings['Qgs_PrefixPath'])
    if not isExist:
        
        logger.error('Qgs_PrefixPath not found')
        logger.critical('Program terminated')
        sys.exit()
    else:
        logger.info('Qgs_PrefixPath found')
    
    isExist = os.path.exists(settings['QGIS_Plugin_Path'])
    if not isExist:
        
        logger.error('QGIS_Plugin_Path not found')
        logger.critical('Program terminated')
        sys.exit()
    else:
        logger.info('QGIS_Plugin_Path found')

    isExist = os.path.exists(settings['QGIS_bin_folder'])
    if not isExist:
        
        logger.error('QGIS_Bin_Folder not found')
        logger.critical('Program terminated')
        sys.exit()
    else:
        logger.info('QGIS_Bin_Folder found')

    ## Locating the logdir
    isExist = os.path.exists(settings['logdir'])
    if not isExist:
        logger.error('Logdir does not exist')
        logger.critical('Program terminated')
        sys.exit()
    else:
        logger.info('Logdir found')

    if settings['logdir'][-1] != '/':
        settings['logdir'] = settings['logdir'] + '/'

    ## Locating the temp folder
    isExist = os.path.exists(settings['TempFolder'])
    if not isExist:
        logger.error('TempFolder does not exist')
        logger.critical('Program terminated')
        sys.exit()
    else:
        logger.info('TempFolder found')
    if settings['TempFolder'][-1] != '/':
        settings['TempFolder'] = settings['TempFolder'] + '/'

    logger.info('')  
    logger.info('Environement and settings OK !')     

def describeEngine(scriptfolder, algorithms, version):
    logger = get_logger()
    qgis_supported = get_qgis_support()

    try:
        supported = qgis_supported[version]
    except:
        supported = 'Not tested'
    try:
        import psutil
    except ImportError:
        pip.main(['install', 'psutil'])
        import psutil

    info={}
    info['platform']=platform.system()
    info['platform-release']=platform.release()
    info['platform-version']=platform.version()
    info['architecture']=platform.machine()
    info['hostname']=socket.gethostname()
    info['ip-address']=socket.gethostbyname(socket.gethostname())
    info['mac-address']=':'.join(re.findall('..', '%012x' % uuid.getnode()))
    info['processor']=platform.processor()
    try:
        info['ram']=str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB"
        info['cores'] = psutil.cpu_count()
    except:
        info['ram'] ='Not available'

    logger.info("")
    logger.info("##################################################")
    logger.info("Initializing engine:                              ")
    logger.info("Platform: " + info['platform'] + " " + info['platform-release'] + " ")
    logger.info("Platform version: " + info['platform-version'] + " ")
    logger.info("Architecture: " + info['architecture'] + " ")
    logger.info("Processor: " + info['processor'] +  " ")
    logger.info("Number of cores : " + str(info['cores']) + " ")
    logger.info("Available memmory: " + info['ram'] + " ")
    logger.info("")
    logger.info("QGIS version: " + str(version) + "                ")
    logger.info("QGIS ETL status: " + str(supported) + "                ")
    logger.info("Script folder: " + str(scriptfolder) + "")
    algs = []
    for s in algorithms:
        algs.append(s.displayName()) 
    logger.info("Available custom Scripts : " + str(algs) + "")
    logger.info("##################################################")
    logger.info("QGIS ETL engine ready")
    logger.info("")
    logger.info("----- Starting Script -----")


def get_config():
    settings_file =  path.abspath(path.join(argv[0] ,"../..")) + '\\settings.json'

    with open(settings_file, 'r') as file:
        settings = json.load(file)

    return settings

def get_qgis_support():
    inputfile =  path.abspath(path.join(argv[0] ,"../..")) + '\\qgis_versions.json'
    with open(inputfile, 'r') as file:
        qgis_support = json.load(file)
    return qgis_support

def get_postgres_connections(settings):
    ini = QSettings(settings['QGIS_ini_Path'], QSettings.IniFormat)
    connections = []

    keys = ini.allKeys()
    for elm in keys:
        if 'PostgreSQL' in elm:
            if 'port' in elm :
                            
                connection = elm.split('PostgreSQL/connections/')[1].split('/')[0]
                connections.append(connection)

    return connections

def get_bin_folder(settings):
    logger = get_logger()
    if 'OSGeo4W' in settings['Qgs_PrefixPath']:
        logger.info("QGIS installed in OSGeo4W bundle")
        bin = path.abspath(path.join(settings['Qgs_PrefixPath'] ,"../..")) + '\\bin\\'

    else:
        logger.info("QGIS installed standalone")
        bin = settings['Qgs_PrefixPath'] + '\\bin\\'

    return bin

def script_finished():
    logger = get_logger()
    now = datetime.now()
    logger.info('')
    logger.info('##################################################')
    logger.info('JOB: ' + argv[0] + ' FINISHED')
    logger.info('ENDTIME: ' + now.strftime("%d/%m/%Y, %H:%M"))
    logger.info('##################################################')

def script_failed():
    logger = get_logger()
    now = datetime.now()
    logger.info('')
    logger.info('##################################################')
    logger.info('JOB: ' + argv[0] + ' FAILED')
    logger.info('ENDTIME: ' + now.strftime("%d/%m/%Y, %H:%M"))
    logger.info('##################################################')
    sys.exit()
    



