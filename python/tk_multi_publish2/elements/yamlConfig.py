#
#
#
# reading a per-project yaml config file and returning values
#
#

from os.path import join, exists, dirname
from sys import path

def yamlConfigFile(configLocation):
	'''passed a sgtk config location (as returned from sgtk.pipeline_configuration.get_config_location()), return the location of an 
		elements yaml config file if it exists, None if not'''
	
	configFile=join(configLocation, "phosphene", "elements", "ingest.yml")
	
	print "checking for per-project yaml config file at "+str(configFile)
	
	if exists(configFile):
		return configFile
	else:
		return None
	
def parseYAML(configFile):
	'''passed a config file, will attempt to parse it as a yaml config for the elements ingest tool
	
	   if yaml is not already in the pythonpath, will append the config directory to the path and try again, so you can include the yaml
	   libraries in the same folder as the config file
	'''
	
	try:
		import yaml
	except:
		path.append(dirname(configFile))
		
		import yaml
		
	with open(configFile, 'r') as myFile:
		results=yaml.load(myFile)
		
	return results
		
		