import boto3
import yaml
import sys
import json
from botocore.exceptions import ClientError

def load_profiles(yaml_file):
    with open(yaml_file, 'r') as file:
        return yaml.safe_load(file)

def update_yaml_file(yaml_file, profile_name, arn):
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
        
        # Update the model_id for the matching profile
        for app in data['apps']:
            if app['name'] == profile_name:
                app['created_model_id'] = arn
                break
        
        # Write back to yaml file
        with open(yaml_file, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
        print(f"\nUpdated YAML file with ARN for profile: {profile_name}")
    except Exception as e:
        print(f"Error updating YAML file: {e}")

def create_inference_profile(client, app):
    try:
        response = client.create_inference_profile(
            inferenceProfileName=app['name'],
            description=app.get('description', ''),
            clientRequestToken="123458",
            tags=app.get('tags', []),
            modelSource={
                'copyFrom': app.get('model_id')
            }
        )
        print("\nCreate Inference Profile Response:")
        print("Full API Response:", json.dumps(response, default=str, indent=2))
        
        # Update YAML with the new ARN
        if 'inferenceProfileArn' in response:
            update_yaml_file('profiles.yaml', app['name'], response['inferenceProfileArn'])
        
        return response
    except ClientError as e:
        print(f"Error creating inference profile: {e}")
        return None

def update_inference_profile(client, app):
    try:
        response = client.update_inference_profile(
            name=app['name'],
            type=app['type'],
            description=app.get('description', ''),
            modelId=app.get('model_id', '')
        )
        print("\nUpdate Inference Profile Response:")
        print(f"Profile Name: {response.get('name')}")
        print(f"Status: {response.get('status')}")
        print(f"Last Modified: {response.get('lastModifiedTime')}")
        print("-" * 50)
        return response
    except ClientError as e:
        print(f"Error updating inference profile: {e}")
        return None

def delete_inference_profile(client, profile_name):
    try:
        response = client.delete_inference_profile(
            name=profile_name
        )
        print("\nDelete Inference Profile Response:")
        print(f"Profile Name: {profile_name}")
        print(f"Status: {response.get('status')}")
        print(f"Deletion Time: {response.get('deletionTime')}")
        print("-" * 50)
        return response
    except ClientError as e:
        print(f"Error deleting inference profile: {e}")
        return None

def list_inference_profiles(client):
    try:
        response = client.list_inference_profiles()
        profiles = response.get('inferenceProfiles', [])
        print("\nList of Inference Profiles:")
        for profile in profiles:
            print(f"\nProfile Name: {profile.get('inferenceProfileName')}")
            print(f"Profile ARN: {profile.get('inferenceProfileArn')}")
            print(f"Description: {profile.get('description')}")
            print(f"Status: {profile.get('status')}")
            print(f"Created: {profile.get('creationTime')}")
            print(f"Last Modified: {profile.get('lastModifiedTime')}")
            print("-" * 50)
        return response
    except ClientError as e:
        print(f"Error listing inference profiles: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_inference_profile.py <action> [profile_name]")
        print("Actions: create, update, delete, list")
        sys.exit(1)

    action = sys.argv[1]
    profile_name = sys.argv[2] if len(sys.argv) > 2 else None

    # Load profiles from YAML
    profiles = load_profiles('profiles.yaml')
    
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock', region_name='ap-southeast-2')
    
    if action == 'list':
        list_inference_profiles(bedrock)
    elif action == 'create':
        for app in profiles['apps']:
            create_inference_profile(bedrock, app)
    elif action == 'update':
        for app in profiles['apps']:
            if not profile_name or app['name'] == profile_name:
                update_inference_profile(bedrock, app)
    elif action == 'delete':
        if profile_name:
            delete_inference_profile(bedrock, profile_name)
        else:
            print("Profile name required for delete action")
    else:
        print("Invalid action. Use: create, update, delete, or list")

if __name__ == "__main__":
    main()
