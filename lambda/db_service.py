import os
import boto3

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

def get_db_adapter():
    ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
    ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')
    
    ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
    return DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)