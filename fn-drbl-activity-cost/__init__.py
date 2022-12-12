import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timezone
from azure.mgmt.costmanagement.models import ( QueryDefinition, ExportType, TimeframeType, QueryTimePeriod, 
        GranularityType, QueryDataset, QueryAggregation, QueryGrouping)

def main(params) -> dict:
    logging.info('Starting execution of the activity function')     

    try: 
        from_datetime =  datetime.strptime(params['fromDatetime'], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        to_datetime = datetime.strptime(params['toDatetime'], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        cred = DefaultAzureCredential(
            exclude_cli_credential = False,
            exclude_environment_credential = True,
            exclude_managed_identity_credential = True,
            exclude_powershell_credential = True,
            exclude_visual_studio_code_credential = True,
            exclude_shared_token_cache_credential = True,
            exclude_interactive_browser_credential = True,
            visual_studio_code_tenant_id = "8dc94566-ec40-4aad-abe0-739751b9d5b4"
        )        

        cost_mgmt_client = CostManagementClient(cred, 'https://management.azure.com')

        query_dataset = QueryDataset(
            granularity=GranularityType("Daily"),                
            # configuration=QueryDatasetConfiguration(), 
            aggregation={"totalCost" : QueryAggregation(name="PreTaxCost", function ="Sum")}, 
            grouping=[QueryGrouping(type="Dimension", name="ResourceGroup")], 
            # filter = QueryFilter()
        )
        
        query_def = QueryDefinition(
            type=ExportType("Usage"),
            timeframe=TimeframeType("Custom"),            
            time_period=QueryTimePeriod(from_property=from_datetime, to=to_datetime),
            dataset=query_dataset
        )

        query_result = cost_mgmt_client.query.usage(scope=params['scope'], parameters=query_def)

        query_result_dict = query_result.as_dict()
        rows_of_cost = query_result_dict["rows"]
        if(len(rows_of_cost) > 7):
            past_7_days_cost = list()
            for i in range(len(rows_of_cost)-7,len(rows_of_cost)):
                past_7_days_cost.append(rows_of_cost[i][0])
            avg_cost = sum(past_7_days_cost)/7
        else:
            logging.info("Cost data not available for the past 7 days")
        
        if(avg_cost > 23):
            logging.info("Threshold exceeded by {0}".format(abs(avg_cost-23)))
        
        logging.info("Avg Cost: $ {0}".format(avg_cost))
        
        return query_result.as_dict()        

    except Exception as e:
        logging.exception(e)
        return str(e)