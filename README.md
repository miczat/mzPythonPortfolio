# mzPythonPortfolio
My Python Portfolio - examples of my work

##_boilerplate_1.5.py##

This is my template for non-trivial scripts.  It contains code I use often, such as: 
    * documentation
    * library imports
    * environment settings
    * coordinate system references
    * extension checkout
    * logging to the screen and a CSV
    * counting rows
    * generic exception handling

  The header is embedded documentation.  This has been borrowed from my Java lecturer when I was at uni.  It makes for useful, self-describing scripts. Key sections are:
  * The usual description, author, date, and version
  * Pre - means preconditions, what needs to be true for the code to work
  * Param - parameters that are expected to be passed in
  * Return - values/objects that are returned
  * Post-post conditions. Things that are true when the program finishes
  * Issues and limitations 
  * My personal naming conventions for files and parts of file names
  
##spatial_fuzzy_match.py##

This script was used to deduplicate businesses with the same or similar names within a threshold neighborhood distance. ArcPy is used to select features within the neighborhood, and the Python library fuzzywuzzy was used to calculate name similarity using the Levenshtein Distance.  Database queries were used later to find and flag potential duplicates.

##osm_geocode.ipynb##
The Open Routing Service (ORS) was used to geocode 1500 street addresses. ORS has an API accessible via Python, which is implemented in a Python Notebook in this example. Using a free API key, addresses are submitted to ORS, being careful not to exceed the rate limit. Results are written to a CSV file for import into ArcGIS Pro.
