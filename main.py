#!/usr/bin/python3

# Load parameters
from utility import execfileIfNeeded
import inspect, os
parameters = {}
parametersFile = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config/parameters.py"
parametersFileInfo = {}
execfileIfNeeded( parametersFile, parameters, parametersFileInfo )

# Initialize vehicle data with a multithread lock
from threading import Lock
vehicleData = ({},Lock())

# Run the HTTP server
from OBDRelayHTTPServer import OBDRelayHTTPServerThread
httpServers = []
for httpBinding in parameters["httpBindings"]:
	httpd = OBDRelayHTTPServerThread( vehicleData, ipAddress=httpBinding["address"], tcpPort=httpBinding["port"], cacheExpire=httpBinding["cacheExpire"] )
	httpServers.append( httpd )
	httpd.start()
del httpd

# Run the OBD logger
from OBDLogging import OBDLoggingThread
vehicleInterfaceLogger = OBDLoggingThread()
vehicleInterfaceLogger.start()

# Run the ELM327 manager
from OBDRelayELM327 import OBDRelayELM327Thread
vehicleInterface = OBDRelayELM327Thread( vehicleData )
vehicleInterface.attachLoggingThread( vehicleInterfaceLogger )
vehicleInterface.start()

# Reload the parameters
from utility import printT
def reloadParameters():
	if execfileIfNeeded( parametersFile, parameters, parametersFileInfo ):
		for httpBinding in parameters["httpBindings"]:
			for httpd in httpServers:
				httpdParameters = httpd.getParameters()
				# Reload HTTP parameters for the HTTP server matching address & port:
				if httpBinding["address"]==httpdParameters["ipAddress"] and httpBinding["port"]==httpdParameters["tcpPort"]:
					if "cacheExpire" in httpBinding:
						httpd.setCacheExpire( httpBinding["cacheExpire"] )
					else:
						httpd.setCacheExpire()
					break
		printT( "[main.py] Parameters have been reloaded." )



# Main work in an endless loop
try:
	from time import sleep
	while True:
		sleep( 3 )
		reloadParameters()
except KeyboardInterrupt:
	vehicleInterfaceLogger.terminate()
