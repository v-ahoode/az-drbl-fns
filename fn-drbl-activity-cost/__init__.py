import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient
from datetime import datetime, timezone
from azure.mgmt.costmanagement.models import ( QueryDefinition, ExportType, TimeframeType, QueryTimePeriod, 
        GranularityType, QueryDataset, QueryAggregation, QueryGrouping)

def main(params) -> dict:
    logging.info('Starting execution of the activity function')     

    try: 
        from_datetime =  datetime.strptime(params['fromDatetime'], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        to_datetime = datetime.strptime(params['toDatetime'], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        # cred = DefaultAzureCredential(
        #     exclude_cli_credential = False,
        #     exclude_environment_credential = False,
        #     exclude_managed_identity_credential = False,
        #     exclude_powershell_credential = False,
        #     exclude_visual_studio_code_credential = False,
        #     exclude_shared_token_cache_credential = False,
        #     exclude_interactive_browser_credential = False,
        #     visual_studio_code_tenant_id = "8dc94566-ec40-4aad-abe0-739751b9d5b4"
        # )  

        cred = DefaultAzureCredential()  

              
        subscription_id = "edf6dd9d-7c4a-4bca-a997-945f3d60cf4e"

        cost_mgmt_client = CostManagementClient(cred, 'https://management.azure.com')

        resource_mgmt_client = ResourceManagementClient(cred, subscription_id)

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

        resourceGroups = resource_mgmt_client.resource_groups.list()

        rgs_cost_dict = {}

        for rg in list(resourceGroups):
            if rg.managed_by is None:
                scope_with_rg = '' + params['scope'] + str(rg.name)
                query_result = cost_mgmt_client.query.usage(scope=scope_with_rg, parameters=query_def)

                query_result_dict = query_result.as_dict()
                rows_of_cost = query_result_dict["rows"]
                if(len(rows_of_cost) > 7):
                    last_7_days_cost = list()
                    for i in range(len(rows_of_cost)-7,len(rows_of_cost)):
                        last_7_days_cost.append(rows_of_cost[i][0])
                    avg_cost = sum(last_7_days_cost)/7

                    if(avg_cost > 23):
                        logging.info("Threshold exceeded by {0}".format(abs(avg_cost-23)))

                    logging.info("Avg Cost: $ {0}".format(avg_cost))

                    rgs_cost_dict[rg.name] = avg_cost
                else:
                    logging.info("Cost data not available for the past 7 days")
            
        return rgs_cost_dict        

    except Exception as e:
        logging.exception(e)
        return str(e)