import boto3
import os
import time

def create_amplify_app(app_name, repo_url=None, env_vars=None, region="us-east-1"):
    """
    Create an AWS Amplify app using boto3.
    :param app_name: Name of the Amplify app
    :param repo_url: (Optional) Git repository URL to connect
    :param env_vars: (Optional) Dict of environment variables
    :param region: AWS region
    :return: Amplify app ARN
    """
    amplify = boto3.client('amplify', region_name=region)
    params = {
        'name': app_name,
    }
    if repo_url:
        params['repository'] = repo_url
    if env_vars:
        params['environmentVariables'] = env_vars
    response = amplify.create_app(**params)
    print(f"Amplify app created: {response['app']['appArn']}")
    return response['app']['appArn']

def list_amplify_backend_environments(app_id, region="us-east-1"):
    """
    List backend environments for an Amplify app.
    :param app_id: The Amplify app ID
    :param region: AWS region
    :return: List of backend environments
    """
    amplify = boto3.client('amplify', region_name=region)
    response = amplify.list_backend_environments(appId=app_id)
    envs = response.get('backendEnvironments', [])
    print(f"Found {len(envs)} backend environments for app {app_id}.")
    return envs

def get_amplify_backend_environment_details(app_id, environment_name, region="us-east-1"):
    """
    Get details for a specific Amplify backend environment.
    :param app_id: The Amplify app ID
    :param environment_name: The backend environment name
    :param region: AWS region
    :return: Backend environment details
    """
    amplify = boto3.client('amplify', region_name=region)
    response = amplify.get_backend_environment(appId=app_id, environmentName=environment_name)
    print(f"Backend environment details: {response['backendEnvironment']}")
    return response['backendEnvironment']

# Example usage:
# app_arn = create_amplify_app("my-olas-app", repo_url="https://github.com/my/repo.git")
# app_id = app_arn.split("/")[-1]
# envs = list_amplify_backend_environments(app_id)
# if envs:
#     get_amplify_backend_environment_details(app_id, envs[0]['environmentName'])
