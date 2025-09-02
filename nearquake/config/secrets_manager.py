import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

_logger = logging.getLogger(__name__)


def get_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Retrieve a secret from AWS Secrets Manager.

    :param secret_name: Name of the secret to retrieve
    :param region_name: AWS region name
    :return: Dictionary containing the secret values
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        _logger.error(f"Failed to retrieve secret from AWS Secrets Manager: {e}")
        raise e

    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def get_postgres_secret(region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Retrieve PostgreSQL secrets from AWS Secrets Manager.

    :param region_name: AWS region name
    :return: Dictionary containing the postgres secret values
    """
    return get_secret("nearquake/postgres", region_name)


def get_nearquake_secret(region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Retrieve Nearquake application secrets from AWS Secrets Manager.

    :param region_name: AWS region name
    :return: Dictionary containing the nearquake secret values
    """
    return get_secret("nearquake/secrets", region_name)
