#!/usr/bin/python3

# config
JSAP_FILE = "jamendo.jsap"
CONFIG_FILE = "jamendoWT.conf"

# global reqs
import time
import vamp
import logging
import subprocess
import configparser
from sepy.JSAPObject import *

# local reqs
from lib.Device import *
from lib.ActionHandler import *

# main
if __name__ == "__main__":

    # read jamendo key
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    clientID = config["Jamendo"]["clientId"]

    
    # initialize the logging system
    logger = logging.getLogger('jamendoWT')
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.debug("Logging subsystem initialized")

    # 1 - create an instance of the Device and one of the JSAP
    wt = Device(JSAP_FILE, "jamendoWT", clientID)
    jsap = JSAPObject(JSAP_FILE, 40)
    
    # 2 - specify actions
    wt.addAction("searchWithJamendo", None, [
        {"fieldName":"searchPattern", "fieldType": "http://www.w3.org/2001/XMLSchema#String"}
    ])
     
    # 3 - subscribe to action requests
    wt.waitForActions(ActionHandler)
    
    # 8 - wait, then destroy data
    logging.info("WebThing ready! Waiting for actions!")
    try:
        input("Press <ENTER> to close the WebThing")
        logging.debug("Closing WebThing")
        wt.deleteWT()
    except KeyboardInterrupt:
        logging.debug("Closing WebThing")
        wt.deleteWT()
