#!/usr/bin/python3

# reqs
from sepy.SEPAClient import *
from sepy.YSAPObject import *
import requests
import logging
import json
import sys

# namespaces
qmul = "http://eecs.qmul.ac.uk/wot#"

# settings
updateURI = "http://localhost:8000/update"
subscribeURI = "ws://localhost:9000/subscribe"

# jamendo
NAMESEARCH_URL = "http://api.jamendo.com/v3.0/tracks?client_id=%s&fuzzytags=%s"
clientID = "7a4abfcc"

remove_actions = """PREFIX qmul:<http://eecs.qmul.ac.uk/wot#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wot: <http://wot.arces.unibo.it/sepa#>
PREFIX td: <http://wot.arces.unibo.it/ontology/web_of_things#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
DELETE {{
  <{actionURI}> rdf:type wot:Action .
  <{actionURI}> wot:hasInstance ?actionInstance .
  ?actionInstance wot:hasInputData ?inputData .
  ?inputData dul:hasDataValue ?dataValue
}}
WHERE {{
  <{actionURI}> rdf:type wot:Action .
  <{actionURI}> wot:hasInstance ?actionInstance .
  ?actionInstance wot:hasInputData ?inputData .
  ?inputData dul:hasDataValue ?dataValue
}}"""


sub_to_actions = """PREFIX qmul:<http://eecs.qmul.ac.uk/wot#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wot: <http://wot.arces.unibo.it/sepa#>
PREFIX td: <http://wot.arces.unibo.it/ontology/web_of_things#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?actionInstance ?inputData ?dataValue ?outputData
WHERE {{
  <{thingURI}> wot:hasTD <{thingDescURI}> .
  <{thingDescURI}> wot:hasInteractionPattern <{actionURI}> .
  <{actionURI}> wot:hasInstance ?actionInstance .
  ?actionInstance wot:hasInputData ?inputData .
  ?inputData dul:hasDataValue ?dataValue .
  ?actionInstance wot:hasOutputData ?outputData
}}"""


action_output = """PREFIX qmul:<http://eecs.qmul.ac.uk/wot#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wot: <http://wot.arces.unibo.it/sepa#>
PREFIX td: <http://wot.arces.unibo.it/ontology/web_of_things#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc: <http://purl.org/dc/elements/1.1>
PREFIX ac: <http://audiocommons.org/ns/audiocommons#>
INSERT DATA {{ GRAPH <{graph}> {{  
  {triples}
}} }}"""

class ActionHandler:

    def __init__(self, kp):
        self.counter = 0
        self.kp = kp

    def handle(self, added, removed):

        try:
        
        # check if it is the first request
            if (self.counter > 0):
    
                # debug message
                print("Search request #%s" % self.counter)
                
                # cycle over added bindings
                for a in added:
                    
                    # read the input
                    print("callback 1")
                    inputData = json.loads(a["dataValue"]["value"])
                    outputGraph = a["outputData"]["value"]
                    
                    # search on jamendo
                    print("callback 2")
                    searchPattern = "+".join(inputData["tags"])
                    r = requests.get(NAMESEARCH_URL % (clientID, searchPattern))
                    print("Asking Jamendo for songs matching %s" % searchPattern)
                    res = json.loads(r.text)
                    print(res)
                    print("callback 3")
    
                    # iterate on results and put them in the named graph
                    triples = []
                    for r in res["results"]:                
                        triples.append(" <%s> rdf:type ac:AudioClip " % r["shorturl"])
                        triples.append(" <%s> dc:title '%s' " % (r["shorturl"], r["name"]))
                        triples.append(" <%s> ac:available_as <%s>  " % (r["shorturl"], r["shareurl"]))
                        triples.append(" <%s> rdf:type ac:AudioFile " % r["shareurl"])                    
                    tl = ".".join(triples)
                    print(action_output.format(
                        graph = outputGraph,
                        triples = tl
                    ))
                    print("PRE UPDATE")
                    self.kp.update(updateURI, action_output.format(
                        graph = outputGraph,
                        triples = tl
                    ))                
                    print("POST UPDATE")
                    
                    # add results            
    
            # increment requests
            self.counter += 1

        except:
            pdb.set_trace()
            
# main
if __name__ == "__main__":

    # create a new KP
    #kp = LowLevelKP(None, 40)
    kp = SEPAClient(None, 40)

    # create an YSAPObject
    ysap = YSAPObject("jamendoTD.yaml", 40)
    
    # create URIs for
    # - thing
    # - thingDescription
    # - search action
    # - search action dataschema
    thingURI = qmul + "JamendoWT"
    thingDescURI = qmul + "JamendoWT_TD"
    actionURI = qmul + "searchAction"
    indataSchemaURI = qmul + "searchAction_IDS"
    outdataSchemaURI = qmul + "searchAction_ODS"

    # get the first update (TD_INIT)
    updText = ysap.getUpdate("TD_INIT",
                             {"thingURI": " <%s> " % thingURI,
                              "thingDescURI": " <%s> " % thingDescURI,
                              "thingName":" 'JamendoWT' "})
    kp.update(ysap.updateURI, updText)
    
    # get the second update (TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT)
    updText = ysap.getUpdate("TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT",
                             {"thingDescURI": " <%s> " % thingDescURI,
                              "actionURI": " <%s> " % actionURI,
                              "actionName": " 'searchByTags' ",                              
                              "inDataSchema": " <%s> " % indataSchemaURI,
                              "outDataSchema": " <%s> " % outdataSchemaURI,
                              "actionComment": " 'Search song by tags' "
                             })
    kp.update(ysap.updateURI, updText)
        
    # # remove existing action instances
    # kp.update(updateURI, remove_actions.format(
    #     actionURI = actionURI
    # ))
    
    # # put the thing description    
    # kp.update(updateURI, init_td.format(
    #     thingURI = thingURI,
    #     thingName = "JamendoWT",
    #     thingDescURI = thingDescURI,
    #     actionURI = actionURI,
    #     actionName = "Search",
    #     actionComment = "Search using tags",
    #     actionDataSchema = dataSchemaURI
    # ))

    # # subscribe
    # kp.subscribe(subscribeURI, sub_to_actions.format(
    #     thingURI = thingURI,
    #     thingDescURI = thingDescURI,
    #     actionURI = actionURI,
    # ), "actions", ActionHandler(kp))

    # wait
    logging.info("WebThing ready! Waiting for actions!")
    try:
       input("Press <ENTER> to close the WebThing")
       logging.debug("Closing WebThing")

       # delete action and instances
       updText = ysap.getUpdate("TD_DELETE_ACTION_STRING_INPUT_GRAPH_OUTPUT",
                                {"thingDescURI": " <%s> " % thingDescURI,
                                 "actionURI": " <%s> " % actionURI,
                                })
       kp.update(ysap.updateURI, updText)
       
       # delete thing description
       updText = ysap.getUpdate("TD_DELETE",
                                {"thingURI": " <%s> " % thingURI})
       kp.update(ysap.updateURI, updText)
       
    except KeyboardInterrupt:
       logging.debug("Closing WebThing")
