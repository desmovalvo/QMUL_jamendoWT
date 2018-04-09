#!/usr/bin/python3

# global reqs
import json
import uuid
import logging
import requests
from rdflib import *

# constants
QMUL = "http://eecs.qmul.ac.uk/wot#"
NAMESEARCH_URL = "http://api.jamendo.com/v3.0/tracks?client_id=%s&namesearch=%s"

class ActionHandler:

    """This class is used to handle the action requests"""

    # constructor
    def __init__(self, kp, jsap, clientID):

        """Constructor of the handler"""

        # debug message
        logging.debug("ActionHandler::__init__() invoked")

        # store the kp and the jsap object
        self.clientID = clientID
        self.jsap = jsap
        self.kp = kp
        

    def handle(self, added, removed):

        """This method is triggered every time a notification or a ping arrives"""

        # parse the message
        logging.debug(added)
        logging.debug(removed)
        
        # debug message
        logging.debug("ActionHandler::handle() invoked")

        # we need to get all data related to the action , the song name and the transform
        actionInstance = None
        transformUri = None
        songName = None
        
        # iterate over added building
        # TODO -- consider that we may receive multiple action requests with a notification
        #         but for the demo purposes it is not mandatory
        if len(added) > 0:
            for result in added:
                actionInstance = result["instance"]["value"]
                if result["fieldName"]["value"] == "searchPattern":
                    searchPattern = result["fieldValue"]["value"]
    
                    # do stuff!
                    r = requests.get(NAMESEARCH_URL % (self.clientID, searchPattern))
                    res = json.loads(r.text)

                    # create a bag for the results
                    rdfbag = QMUL + str(uuid.uuid4())

                    # put every song in the bag into sepa
                    for r in res["results"]:

                        try:
                            self.kp.update(self.jsap.updateUri, self.jsap.getUpdate("PUT_AUDIOFILE", {
                                "rdfbag": rdfbag,
                                "audiofile": r["shareurl"],
                                "audioclip": r["shorturl"],
                                "title": r["name"]
                            }))
                        except:
                            # fix problems related to utf-8 encoding
                            pass
                    
                    # write the result of the action into SEPA
                    self.kp.update(self.jsap.updateUri, self.jsap.getUpdate("ADD_COMPLETION_TIMESTAMP_WITH_OUTPUT", {
                        "instance": actionInstance,
                        "outputFieldValue": rdfbag,
                        "outputFieldName": "jamendoResultBag"
                    }))
                
            
                    
