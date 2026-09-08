from core.logger import *
from core.misc import get_config
import sys, copy, os
import subprocess
from random import randrange
from qgis.core import QgsVectorFileWriter, QgsVectorLayerExporter, QgsProject, QgsVectorLayer
from core.misc import script_failed, create_tempfile, delete_tempfile

import processing

class Output_Writer:

    logger = get_logger()

    def postgis(layer: QgsVectorLayer, connection : str, dbname: str, schema: str, tablename: str, overwrite: bool = True):
        """
        A function that exports a QgsVectorLayer into a Postgis database.

        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer to be exported into Postgis

        connection : str
            The name of the connection object in the settings file

        dbname : str
            The database name

        schema : str
            Schema name

        tablename : str
            The name of the table that will be imported
        
        overwrite : bool
            Defaults to True. Should the resulting table in Postgis be overwritten if it exists. If set to False, then it will append the data.
        """

        logger.info(f'Exporting {str(layer.featureCount())} features to Postgis')
        tempfile = create_tempfile(layer, 'postgis')
        logger.info('Temporary layer created')

        try:
            config = get_config()
            dbConnection = config['DatabaseConnections'][connection]

            # ogr2ogr parameters
            table = f'-nln "{schema}.{tablename}"'
            ogrconnection = f'PG:"host={dbConnection["host"]} port={dbConnection["port"]} dbname={dbname} schemas={schema} user={dbConnection["user"]} password={dbConnection["password"]}"'
            ogr2ogrstring = f'{config["QGIS_bin_folder"]}/ogr2ogr.exe -f "PostgreSQL" {ogrconnection} {tempfile} {table}'
            if overwrite:
                ogr2ogrstring = f'{ogr2ogrstring} -overwrite'
            logger.info(f'Writing to PostGIS database {dbname}')
            run = subprocess.run(ogr2ogrstring, capture_output=True)
            delete_tempfile(tempfile)
            logger.info('Temporary layer removed')
            logger.info('Export to PostGIS completed')
            
        except Exception as error:
            logger.error("An error occured exporting to Postgis")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def geopackage(layer: QgsVectorLayer, layername: str, geopackage: str, overwrite: bool):
        """
        A function that writes a QgsVectorLayer to a Geopackage file. 

        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer that is to be written to the geopackage

        layername : String
            The name of the layer in the geopackage file

        geopackage : String
            The full path for the geopackage to be created

        overwrite : Boolean

            Specify wheather the writer will overwrite existing geopackage or append layer. Boolean True/False

        """

        logger.info(f'Writing {str(layer.featureCount())} features to geopackage : {geopackage}')
        try:
            layer.setName(layername)
            parameter = {'LAYERS': [layer],
                    'OUTPUT': geopackage,
                    'OVERWRITE': overwrite,
                    'SAVE_STYLES': False,
                    'SAVE_METADATA': False,
                    'SELECTED_FEATURES_ONLY': False}
            processing.run("native:package", parameter)
            logger.info(f'Parameters: {str(parameter)}')
            logger.info("Export to Geopackage completed")
        except Exception as error:
            logger.error("An error occured exporting layer to geopackage")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def append_geopackage(layer: str, layername: str, geopackage: str):
        """
        Append a layer to an existing geopackage.
        If the new layer does not exist, it will be created. It it exists, the features will be appended to the layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer that is to be written to a file

        layername : String
            The name of the layer in the geopackage file

        geopackage : String
            The full path for the geopackage to be created

        """
        logger.info("Running append layer to Geopackage")
        if os.path.isfile(geopackage):
            logger.info(f'Geopackage {geopackage} exists, appending layer')
            tempfile = create_tempfile(layer, 'append_geopackage')

            try:
                config = get_config()
                ## ogr2ogr parameters
                table = f'-nln "{layername}"'
                ogr2ogrstring = f'{config["QGIS_bin_folder"]}/ogr2ogr.exe -f "GPKG" {geopackage} {tempfile} -nln {layername} -update -append'
                logger.info(f'Writing new layer {layername} to: {geopackage}')
                logger.info(f'Ogr2ogr command {ogr2ogrstring}')
                ogr2ogrstring.join(' -progress')
                run = subprocess.run(ogr2ogrstring, stderr=subprocess.STDOUT)
                if run.stdout:
                    logger.info(run.stdout)
                delete_tempfile(tempfile)
                logger.info(f'Append to geopackage completed')

            except Exception as error:
                logger.error("An error occured appending layer to geopackage")
                logger.error(f'{type(error).__name__}  –  {str(error)}')
                logger.critical("Program terminated")
                script_failed() 
        else:
            logger.error("Target geopackage not found")
            logger.critical("Program terminated")
            script_failed()     

    def file(layer: str, path: str, format: str):
        """
        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer that is to be written to a file

        path : _type_
            The full path for the file to be created

        format : _type_
            The driver type used to write the data to the file. 
        """

        logger.info(f'Writing {str(layer.featureCount())} features to: {path}')
        try:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = format
            QgsVectorFileWriter.writeAsVectorFormatV3(layer, path, QgsProject.instance().transformContext(), options)
            logger.info("Export completed")
        except Exception as error:
            logger.error("An error occured exporting layer")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def textfile(file: str, list: list, newline: bool):
        """
        Create an output file from a list of lines. 

        Parameters
        ----------
        file : Path and filename
            The file to be created.
            
        list : List
            List of lines to be written to the file.

        newline : Boolean
            If true, a newline character will be added to the end of each line.
        """
        logger.info("Creating text file: " + file)
        try:
            with open(file, 'w', encoding="utf-8") as f:
                for line in list:
                    if newline == True:
                        f.write(line + '\\n')
                    else:
                        f.write(line)
            logger.info("File created")
        except Exception as error:
            logger.error("An error occured creating file")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def mssql(layer: QgsVectorLayer, connection: str, driver: str, schema: str, table: str, overwrite: str, geom_type: str, geom_name: str, ogr2ogr_params: str):
        """
        A function that exports a QgsVectorLayer into a MSSQL database using ogr2ogr.
        The function writes the data to a temporary geojson file, that is then importet to the database with ogr2ogr.
        
        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer that is to be written to a file.

        connection : String
            The name of a connection from the settings.json file.
        
        driver : String (Optional)
            The driver used for writing to the database.
            Default value is : 'SQL Server'.
            
        schema : String
            The target schema.

        table : String
            The target table.

        overwrite : Boolean
            Overwrite or append.

        geom_type : String
            Geometry type. One of geometry/geography.

        geom_name : String
            Name of the geometry coloumn.

        ogr2ogr_params : String
            Extra parameters for ogr2ogr besides the default.
        """

        try:
            config = get_config()
            logger.info(f'Exporting {layer} to MSSQL Server')
            dbconnection = config['DatabaseConnections'][connection]
            conn = copy.copy(dbconnection)
            conn['password'] = 'xxxxxxx'
            logger.info(f'Connection: {str(conn)}')
            logger.info(f'Creating temporary layer in Temp folder')
            tmp_path = f'{config["TempFolder"]}mssql_layer_{str(randrange(1000))}.geojson'
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GeoJSON'
            QgsVectorFileWriter.writeAsVectorFormatV3(layer, tmp_path, QgsProject.instance().transformContext(), options)
            logger.info('Temporary layer created')

            ## ogr2ogr parameters
            table = f'-nln "{schema}.{table}"'
            geometry = f'-lco "GEOM_TYPE={geom_type}" -lco "GEOM_NAME={geom_name}"'
            
            if driver != '':
                mssql_driver = driver
            else:
                 mssql_driver = 'SQL Server'

            if dbconnection['user'] == '' and dbconnection['password'] == '':
                ogrconnection = f"MSSQL:server={dbconnection['host']};driver={mssql_driver};database={dbconnection['databasename']};trusted_connection=yes;"
            else:
                ogrconnection = f"MSSQL:server={dbconnection['host']};driver=SQL Server;database={dbconnection['databasename']};uid={dbconnection['user']};pwd={dbconnection['password']}"

            if overwrite == True:
                ow = '-overwrite'
            else:
                ow = ''

            if ogr2ogr_params != '':
                ep = ' ' + ogr2ogr_params
            else:
                ep = ''
            
            ogr2ogrstring = f'{config["QGIS_bin_folder"]}/ogr2ogr.exe --config MSSQLSPATIAL_USE_BCP FALSE -f "MSSQLSpatial" "{ogrconnection}" "{tmp_path}" {geometry} {table} -lco UPLOAD_GEOM_FORMAT=wkt {ep}  {ow}'
            logger.info(f'Writing to MSSQL database {dbconnection["databasename"]}, {table}')
            ogr2ogrstring.join(' -progress')
            run = subprocess.run(ogr2ogrstring, stderr=subprocess.STDOUT)
            if run.stdout:
                logger.info(run.stdout)
            os.remove(tmp_path)
            logger.info(f'Export to MSSQL completed')
        
        except Exception as error:
            try:
                os.remove(tmp_path)
            except:
                pass

            logger.error("An error occured exporting to MSSQL")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def filegdb(layer: QgsVectorLayer, layername: str, path: str):
        """
        A function that export a QgsVectorLayer into an ESRI File

        Parameters
        ----------
        layer : QgsVectorLayer
            The layer that is to be written to an ESRI File GeoDatabase
        path : str
            The full path for the ESRI File Geodatabase to be created
        layername : str
            The name of the resulting layer in the ESRI File Geodatabase
        """

        logger.info(f'Writing {str(layer.featureCount())} features to: {path}')
        try:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = layername
            QgsVectorFileWriter.writeAsVectorFormatV3(layer, path, QgsProject.instance().transformContext(), options)
        except Exception as error:
            logger.error("An error occured exporting layer to ESRI File Geodatabase")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated")
            script_failed()

    def packageLayers(layers: list, path: str,  overwrite: bool, style: bool):
        """
        Adds layers to a GeoPackage.
        If the GeoPackage exists and Overwrite existing GeoPackage is checked, 
        it will be overwritten (removed and recreated). 
        If the GeoPackage exists and Overwrite existing GeoPackage is not checked, the layer will be appended.

        Parameters
        ----------
        input : [vector: any] [list]
            The (vector) layers to import into the GeoPackage. 
            Raster layers are not supported. If a raster layer is added, a QgsProcessingException will be thrown.

        overwrite : [boolean]Default: False
            If the specified GeoPackage exists, setting this option to True will make sure that it is deleted 
            and a new one will be created before the layers are added. If set to False, layers will be appended.

        style : [boolean] Default: True
            Save the layer styles

        path : str
            The full path for the Geopackage to be created

        """

        logger.info("Performing packageLayers")
        logger.info(f'Processing {str(len(layers))} layers')
        try:
            parameter = {
                'INPUT': layers,
                'OVERWRITE': overwrite,
                'SAVE_STYLES': style,
                'OUTPUT': path
            }
            logger.info(f'Parameters: {str(parameter)}')
            processing.run('native:package', parameter)['OUTPUT']           
            logger.info("packageLayers finished")
        except Exception as error:
            logger.error("An error occured in packageLayers")
            logger.error(f'{type(error).__name__}  –  {str(error)}')
            logger.critical("Program terminated" )
            script_failed()