from core.logger import *
from core.misc import get_config
import sys
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsVectorLayerExporter
from core.misc import script_failed

import processing
from processing.core.Processing import Processing
from processing.script.ScriptUtils import *
from qgis.analysis import QgsNativeAlgorithms
Processing.initialize()

class Output_Writer:

    logger = get_logger()

    def postgis(layer, dbname, schema, tablename):
        """
        A function that exports a QgsVectorLayer into a Postgis database.

        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer to be exported into Postgis
        dbname : str
            The database name
        schema : str
            Schema name
        tablename : str
            The name of the table that will be imported
        """

        logger.info(f'Exporting {str(layer.featureCount())} features to Postgis')
        try:
            settings = get_config()
            db_con = settings['DatabaseConnections']['MyPostGIS']
            uri = f'dbname=\'{dbname}\' host=\'{db_con["host"]}\' port=\'{db_con["port"]}\' user=\'{db_con["user"]}\' password=\'{db_con["password"]}\' table="{schema}"."{tablename}" (geom) key=\'id\'' 
            QgsVectorLayerExporter.exportLayer(layer, uri, 'postgres', layer.crs())
            logger.info('Export to Postgis completed')
        except Exception as error:
            logger.error('An error occured exporting layer to Postgis')
            logger.error(f'{type(error).__name__} - {str(error)}')
            logger.critical('Program terminated')
            script_failed()

    def geopackage(layer, layername, geopackage, overwrite):
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

        logger.info("Writing "+ str(layer.featureCount()) + " features to geopackage : " + geopackage)
        try:
            layer.setName(layername)
            parameter = {'LAYERS': [layer],
                    'OUTPUT': geopackage,
                    'OVERWRITE': overwrite,
                    'SAVE_STYLES': False,
                    'SAVE_METADATA': False,
                    'SELECTED_FEATURES_ONLY': False}
            processing.run("native:package", parameter)
            logger.info("Parameters: " + str(parameter))
            logger.info("Export to Geopackage completed")
        except Exception as error:
            logger.error("An error occured exporting layer to geopackage")
            logger.error(type(error).__name__ + " – " + str(error))
            logger.critical("Program terminated")
            script_failed()

    def file(layer, path, format):
        """_summary_

        Parameters
        ----------
        layer : QgsVectorLayer
            The QgsVectorLayer that is to be written to a file

        path : _type_
            The full path for the file to be created

        format : _type_
            The driver type used to write the data to the file. 
        """

        logger.info("Writing " + str(layer.featureCount()) + " features to: " + path)
        try:
            QgsVectorFileWriter.writeAsVectorFormat(layer, path, "utf-8", layer.crs(), format)
            logger.info("Export completed")
        except Exception as error:
            logger.error("An error occured exporting layer")
            logger.error(type(error).__name__ + " – " + str(error))
            logger.critical("Program terminated")
            script_failed()

    def textfile(file, list,  newline):
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
            logger.error(type(error).__name__ + " – " + str(error))
            logger.critical("Program terminated")
            script_failed()


