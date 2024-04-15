# ---------------------------------------------------------------------------------------------------------------------
# name:        spatial_fuzzy_match.py
#
# description: Helps find duplicate records in a database that are similar if not identical
#              Designed to be used to find duplicates within one table (the 'left' table). It may be extended to use
#              two tables in the future ('left' and 'right' tables).
#
#              This program compares strings within the search distance and calculates a set of similarity
#              metrics that can be filtered.
#
#              Input data is not case-sensitive. All records are lower-cased at the time of comparison
#              Records with Null geometry are still considered; they are just mapped to (0,0)
#
#              FuzzyWuzzy Levenshtein distance metrics:
#
#                  fw_ratio
#                  fw_partial_ratio
#                  fw_token_sort_ratio
#                  fw_token_set_ratio
#
#              After running this, configure and execute create_lines_from_match_results.py
#
#              Example run times against the Australian Tourism Datawarehouse:
#
#              All ATDW data
#              input rows            1,4683
#              search distance       3600 Meters
#              comparisons made      362,155
#              comparisons skipped   362,153
#              duration              6:12:43.480683"
#              output csv            543 MB
#              log file              1.06 GB
##
#
#
# version      1
# author       Mic Zatorsky
# created      11/09/2020
#
# param:       left_fc_gdb         GDB containing the left feature class (FC)
# param:       left_fc_name        Left FC
# param:       left_fc_text_field  Field containing text to compare
# param:       left_fc_pk          The PK in the left FC
# param:       search_distance     the distance that defines the neighborhood search
# param:       report_folder       the folder to write the output CSV to
# param:       report_name         the name of the CSV file with the pairs of close matches
#
# pre:         the input FC exists
#
# return:      none
#
# post:        a CSV is written with the following structure
#                  left_text
#                  right_text
#                  left_class
#                  right_class
#                  fw_ratio
#                  fw_partial_ratio
#                  fw_token_sort_ratio
#                  fw_token_set_ratio
#                  surrogate_key
#                  left_objectID
#                  right_objectID
#                  left_pk
#                  right_pk
#                  left_x
#                  left_y
#                  right_x
#                  right_y
#
#
# Issues and known limitations:
#     see all preconditions
#     Written for Python 3.6
#     this version works with just one input FC, comparing it with itself
#
# Dev Notes:
#
#     Terminology:
#        Given "C:\TEMP\A.JPG":
#            filepath  =  C:\TEMP\A.JPG
#            folder    =  C:\TEMP
#            filename  =  A.JPG
#            name      =  A
#            ext       =  JPG
#
# Ref:
#     https://www.datacamp.com/community/tutorials/fuzzy-string-python
#     https://towardsdatascience.com/fuzzywuzzy-how-to-measure-string-distance-on-python-4e8852d7c18f
#
# ---------------------------------------------------------------------------------------------------------------------

import arcpy
import logging
import os
import datetime
import uuid
from fuzzywuzzy import fuzz

start_time = datetime.datetime.now()
log = logging.getLogger()

# -----------------------------------------
# run config
# -----------------------------------------
program_name = r"spatial_fuzzy_match.py"
log_folder = r"."

# ATDW vs ATDW
left_fc_gdb = r"C:\Users\mic.zatorsky\Data_Deduplication\Data_Duplication.gdb"
left_fc_name = "ATDW_Staging_pt_included_AND_in_study_area"
left_fc_pk = "Listing_Number"
left_fc_text_field = "tmp_Feature_name"
left_fc_class_field = "tmp_Main_Class"
report_folder = r"C:\Users\mic.zatorsky\Data_Deduplication"
report_filename = "ATDW_fuzzy_comparisons.csv"
search_distance = "3600 Meters"
max_rows_to_process = 1000000    # reduce for testing


# -----------------------------------------
# create and configure the logger
# -----------------------------------------
def setup_logger(log_folder):
    logfile_ext = ".log.csv"
    logfile = os.path.join(log_folder, program_name + logfile_ext)
    log.setLevel(logging.DEBUG)  # or INFO

    # formatter for use by all handlers
    d = ","  # log column delimiter
    log_msg_format_str = '%(asctime)s' + d + '%(levelname)s' + d + '"%(message)s"'
    datetime_fmt_str = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_msg_format_str, datetime_fmt_str)

    # create file handler which logs even debug messages
    try:
        fh = logging.FileHandler(filename=logfile, mode='w')
    except IOError as ioe:
        print("The log file is read only. Program stopping")
        print(repr(ioe))
        raise
    except Exception as e:
        print("An error occurred. Program stopping")
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


# -----------------------------------------
# strip non ascii
# -----------------------------------------
def strip_non_ascii(string):
    """ Returns the string without non ASCII characters"""
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


# ------------------------------------------
#  write list to CSV
# -------------------------------------------

def write_list_to_csv(the_list, the_csv_file_path):
    log.info("Checking if the report file already exists [" + the_csv_file_path + "]")
    if os.path.exists(the_csv_file_path):
        log.info('Deleting existing file')
        try:
            os.remove(the_csv_file_path)
        except Exception as e:
            log.info("Failed to delete the file")
            log.info(repr(e))
            validation_fail = True

    log.info('Creating the CSV file [' + the_csv_file_path + "]")
    with open(the_csv_file_path, "w") as f:
        log.info('Writing the file header')
        header_row = "left_text,right_text,left_class,right_class," \
                     "fw_ratio,fw_partial_ratio,fw_token_sort_ratio,fw_token_set_ratio," \
                     "surrogate_key,left_objectID,right_objectID,left_pk,right_pk,left_x,left_y,right_x,right_y\n"
        f.write(header_row)
        for element in the_list:
            surrogate_key = element.get("surrogate_key")
            left_objectID = element.get("left_objectID")
            right_objectID = element.get("right_objectID")
            left_text = element.get("left_text")
            right_text = element.get("right_text")
            left_class = element.get("left_class")
            right_class = element.get("right_class")
            left_x = element.get("left_x")
            left_y = element.get("left_y")
            right_x = element.get("right_x")
            right_y = element.get("right_y")
            left_pk = element.get("left_pk")
            right_pk = element.get("right_pk")
            fw_ratio = element.get("fw_ratio")
            fw_partial_ratio = element.get("fw_partial_ratio")
            fw_token_sort_ratio = element.get("fw_token_sort_ratio")
            fw_token_set_ratio = element.get("fw_token_set_ratio")

            record = f'"{left_text}","{right_text}","{left_class}","{right_class}",' \
                     f'{fw_ratio},{fw_partial_ratio},{fw_token_sort_ratio},{fw_token_set_ratio},' \
                     f'{surrogate_key},{left_objectID},{right_objectID},"{left_pk}","{right_pk}",' \
                     f'{left_x},{left_y},{right_x},{right_y}'
            # log.debug("Writing row = [" + record + "]")
            f.write(record + "\n")


# -----------------------------------------
# main
# -----------------------------------------

def main():
    """main"""

    log.info('Start')

    # init some vars
    compared_set = set()  # the set of object IDs we have already compared, used to avoid doing things twice
    comparison_list = []  # a list of all comparisons
    skipped_comparison_count = 0  # tracking how often we don't have to calc similarity

    # lets get into it
    left_fc = left_fc_gdb + "\\" + left_fc_name
    arcpy.MakeFeatureLayer_management(left_fc, "left_fc_lyr")
    input_rows_count = int(arcpy.GetCount_management("left_fc_lyr")[0])
    log.info("{} input rows to process".format(input_rows_count))
    fields = ["OBJECTID", left_fc_text_field, "SHAPE@X", "SHAPE@Y", left_fc_pk, left_fc_class_field]
    current_row = 0
    with arcpy.da.SearchCursor("left_fc_lyr", fields) as fc_cursor:
        for fc_cursor_row in fc_cursor:
            left_objectID = fc_cursor_row[0]
            left_text = strip_non_ascii(fc_cursor_row[1])
            left_x = fc_cursor_row[2]
            left_y = fc_cursor_row[3]
            left_pk = fc_cursor_row[4]
            left_class = strip_non_ascii(fc_cursor_row[5])
            log.debug("fc LEFT cursor read id:{} text:{} x:{} y:{} pk:{} class:{}".format(left_objectID, left_text,
                                                                                          left_x, left_y, left_pk,
                                                                                          left_class))

            # fix issue with missing coords (NULLS in the original data)
            if left_x is not None:
                left_x = str(round(fc_cursor_row[2], 8))
            else:
                left_x = str(0)

            if left_y is not None:
                left_y = str(round(fc_cursor_row[3], 8))
            else:
                left_y = str(0)

            log.debug("Searching " + search_distance + " around OBJECTID [" + str(left_objectID) + "] " + left_text)

            # select this record
            arcpy.SelectLayerByAttribute_management(in_layer_or_view="left_fc_lyr",
                                                    selection_type="NEW_SELECTION",
                                                    where_clause="OBJECTID = {}".format(left_objectID))

            # select nearby records within the search distance
            arcpy.SelectLayerByLocation_management(in_layer="left_fc_lyr",
                                                   overlap_type="WITHIN_A_DISTANCE",
                                                   select_features="left_fc_lyr",
                                                   search_distance=search_distance,
                                                   selection_type="NEW_SELECTION",
                                                   invert_spatial_relationship="NOT_INVERT")

            row_count = int(arcpy.GetCount_management("left_fc_lyr")[0])
            log.debug("{} records within search distance, comparing".format(row_count))

            with arcpy.da.SearchCursor("left_fc_lyr", fields) as sel_cursor:
                for sel_cursor_row in sel_cursor:
                    surrogate_key = str(uuid.uuid4())  # generate a GUID for this row
                    right_objectID = sel_cursor_row[0]
                    right_text = strip_non_ascii(sel_cursor_row[1])
                    right_x = str(round(sel_cursor_row[2], 8))
                    right_y = str(round(sel_cursor_row[3], 8))
                    right_pk = sel_cursor_row[4]
                    right_class = strip_non_ascii(sel_cursor_row[5])
                    log.debug(
                        "sel RIGHT cursor read id:{} text:{} x:{} y:{} pk:{} class:{}".format(right_objectID, right_text,
                                                                                              right_x, right_y, right_pk,
                                                                                              right_class))

                    if left_objectID != right_objectID:  # don't compare a record with itself
                        this_pair = str(left_objectID) + "," + str(right_objectID)
                        inverse_of_this_pair = str(right_objectID) + "," + str(left_objectID)
                        if this_pair not in compared_set:

                            # calculate fuzzy similarity metrics

                            fw_ratio = fuzz.ratio(left_text.lower(), right_text.lower())
                            fw_partial_ratio = fuzz.partial_ratio(left_text.lower(), right_text.lower())
                            fw_token_sort_ratio = fuzz.token_sort_ratio(left_text.lower(), right_text.lower())
                            fw_token_set_ratio = fuzz.token_set_ratio(left_text.lower(), right_text.lower())

                            this_match_dict = {}
                            this_match_dict.update({"surrogate_key": surrogate_key})
                            this_match_dict.update({"left_objectID": left_objectID})
                            this_match_dict.update({"right_objectID": right_objectID})
                            this_match_dict.update({"left_text": left_text})
                            this_match_dict.update({"right_text": right_text})
                            this_match_dict.update({"left_class": left_class})
                            this_match_dict.update({"right_class": right_class})
                            this_match_dict.update({"left_x": left_x})
                            this_match_dict.update({"left_y": left_y})
                            this_match_dict.update({"right_x": right_x})
                            this_match_dict.update({"right_y": right_y})
                            this_match_dict.update({"left_pk": left_pk})
                            this_match_dict.update({"right_pk": right_pk})
                            this_match_dict.update({"fw_ratio": fw_ratio})
                            this_match_dict.update({"fw_partial_ratio": fw_partial_ratio})
                            this_match_dict.update({"fw_token_sort_ratio": fw_token_sort_ratio})
                            this_match_dict.update({"fw_token_set_ratio": fw_token_set_ratio})

                            log.debug("Appending pair to the comparison list")
                            comparison_list.append(this_match_dict)

                            compared_set.add(this_pair)
                            compared_set.add(inverse_of_this_pair)

                        else:
                            log.debug("skipping comparison")
                            skipped_comparison_count = skipped_comparison_count + 1

            # progress indicator
            current_row = current_row + 1
            percent_complete = (current_row / input_rows_count) * 100
            log.info("{number: .{precision}f} % complete".format(number=percent_complete, precision=3))

            # stop after the first few
            if current_row >= max_rows_to_process:
                break

    # ---------------------------------
    # write the results to CSV
    # --------------------------------

    report_filepath = os.path.join(report_folder, report_filename)
    write_list_to_csv(comparison_list, report_filepath)

    # --------
    # wrap up
    # --------
    log.info("Finished")
    log.info("input rows            {}".format(input_rows_count))
    log.info("search distance       {}".format(search_distance))
    log.info("comparisons made      {}".format(len(comparison_list)))
    log.info("comparisons skipped   {}".format(skipped_comparison_count))

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    log.info("duration              {}".format(duration))

    # close the log to release locks
    log.info('closing log')
    log_handlers_list = list(log.handlers)
    for h in log_handlers_list:
        log.removeHandler(h)
        h.flush()
        h.close()


if __name__ == "__main__":
    setup_logger(log_folder)
    main()
