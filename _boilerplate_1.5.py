# ---------------------------------------------------------------------------------------------------------------------
# name:        -.py
#
# description: -
#              -
#              -
#
# version      1.5
# author       Mic Zatorsky
# date:        DD/MM/YY
#
# param:       input parameter
#
# pre:         pre-condition
#
# return:      returned value
#
# post:        post-conditions
# 
#
#
# Issues and known limitations:
#     see all preconditions
#     Writen for Python 3.9.18 as shipped with ArcGIS Pro 3.2.2
#
# Dev Notes:
#
#     For processes that require Esri extensions, see the list of extension names here:
#     https://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-functions/checkoutextension.htm
#
#     Terminology:
#        Given "C:\TEMP\A.JPG":
#            filepath   =  C:\TEMP\A.JPG
#            folderpath =  C:\TEMP
#            foldername =  TEMP
#            filename   =  A.JPG
#            name       =  A 
#            extension  =  JPG 
#
#
# Ref:
#     https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/checkoutextension.htm
#      
# ---------------------------------------------------------------------------------------------------------------------


# remove where not used
import arcpy
from arcpy import env
from arcpy.sa import *
import logging
import os
import datetime
import sys
import traceback
import csv

start_time = datetime.datetime.now()
log = logging.getLogger()

# -----------------------------------------
# run config
# -----------------------------------------
log_name = r"progam name here"
log_folder = r"."


# input parameters

# output parameters

# other config

# set the geoprocessing environment
arcpy.env.workspace = r'c:\Temp'   # fGDB or folder
arcpy.env.overwriteOutput = True   # avoids having to test for existence and delete
arcpy.env.addOutputsToMap = False

# remove the one you don't want
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference('GDA 1994 MGA Zone 55')
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(28356)  # MGA Zone 56 by ESPG code
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference('Geocentric Datum of Australia 1994')

# for raster analysis 
arcpy.env.extent = None
arcpy.env.snapRaster = None

# List required extensions here (if any)
required_extensions = ['3D', 'Spatial', 'DataInteroperability', 'Network']  # remove that which is not required


# -----------------------------------------
# create and configure the logger
# -----------------------------------------
def setup_logger(log_folder):
    logfile_ext = '.log.csv'
    logfile = os.path.join(log_folder, log_name + logfile_ext)

    # formatter for use by all handlers
    d = ","   # log column delimiter
    # log_msg_format_str = '%(asctime)s' + d + '%(levelname)s' + d + '"%(message)s"'
    log_msg_format_str = f'%(asctime)s{d}%(levelname)s{d}"%(message)s"'
    datetime_fmt_str = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_msg_format_str, datetime_fmt_str)

    # create file handler which logs even debug messages
    try:
        fh = logging.FileHandler(filename=logfile, mode='w')
    except IOError as ioe:
        print('The log file is read only. Program stopping')
        print(repr(ioe))
        raise
    except Exception as e:
        print('An error occurred. Program stopping')
        print(repr(e))
        raise

    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    log.setLevel(logging.DEBUG)    # or INFO to be less verbose


# -----------------------------------------
# get row count
# -----------------------------------------
def get_row_count(tbl_or_lyr) -> int:
    """Count rows in a table or layer
    
    :param tbl_or_lyr: the name of the table to create
    :returns: int: The count of rows
    :raises None
    """
    row_count = int(arcpy.GetCount_management(tbl_or_lyr)[0])
    log.debug(f"{row_count} rows in {tbl_or_lyr}")
    return row_count
   

# -----------------------------------------
# main
# -----------------------------------------

def main():
    """main"""
    log.info('Start')

    log.info(f'Using Python version {sys.version}')

    log.info('Checking out Extensions')  # as defined in the run config
    arcpy.CheckOutExtension(required_extensions)

    # Productive code goes here
    try:
        log.info('Trying...')
        # do stuff

    except arcpy.ExecuteError as ee:
        log.error('The file may not exist. Program stopping')
        error_value = sys.exc_info()[1]
        log.error(error_value.args[0].replace(',', ' ').strip().replace('\r', '').replace('\n', ''))
        sys.exit()

    except Exception as e:
        error_value = sys.exc_info()[1]
        error_traceback = sys.exc_info()[2]
        tbinfo = traceback.format_tb(error_traceback)[0]
        log.error("SOMETHING ELSE WENT WRONG")
        log.error(error_value.args[0].replace(',', ' ').strip().replace('\r', '').replace('\n', ''))
        log.error(tbinfo.replace(',', ' ').strip().replace('\r', '').replace('\n', ''))
        raise

    # wrap up
    log.info('Finished')
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    log.info(f'Duration          {duration}')

    # close the log to release locks
    log.debug('Closing log')
    log_handlers_list = list(log.handlers)
    for h in log_handlers_list:
        log.removeHandler(h)
        h.flush()
        h.close()


# program entry point when called from the command line
if __name__ == '__main__':
    setup_logger(log_folder)
    main()