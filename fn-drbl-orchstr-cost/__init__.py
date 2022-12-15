import logging
import json
import os
from datetime import datetime
import time 
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    logging.info("Starting execution of orchastrator function")

    #Get parameters from input
    params = context.get_input()            
    
    get_resource_cost_params = {        
       'fromDatetime' : params['fromDatetime'],
       'toDatetime' : params['toDatetime'],
       'scope': params['scope']
    }
    
    get_resource_cost = yield context.call_activity('fn-drbl-activity-cost', get_resource_cost_params)

    logging.info(f"Output of activity fn: '{get_resource_cost}'")
    
    return [get_resource_cost]

main = df.Orchestrator.create(orchestrator_function)