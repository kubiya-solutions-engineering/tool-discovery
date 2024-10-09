#!/usr/bin/env python3

import os
import requests
import json
import argparse

def _get_or_raise_env_var(env_var):
    value = os.getenv(env_var)
    if value is None:
        raise Exception(f"Env var {env_var} is not set")
    return value

# Function to create a service ticket
def create_ticket(description, servicename, title, incident_url, slackincidentcommander, slackdetectionmethod, slackbusinessimpact, incident_id):
    FSAPI_PROD = _get_or_raise_env_var('FSAPI_PROD')
    url = "https://aenetworks.freshservice.com/api/v2/tickets"
    payload = {
        "description": f"{description}</br><strong>Incident Commander:</strong>{slackincidentcommander}</br><strong>Detection Method:</strong>{slackdetectionmethod}</br><strong>Business Impact:</strong>{slackbusinessimpact}</br><strong>Ticket Link:</strong>{incident_url}",
        "subject": f"TESTING {servicename} - {title}",
        "email": "devsecops@aenetworks.com",
        "priority": 1,
        "status": 2,
        "source": 8,
        "category": "DevOps",
        "sub_category": "Pageout",
        "tags": [f"PDID_{incident_id}"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, auth=(FSAPI_PROD, 'X'), headers=headers, json=payload)
    with open('response.json', 'w') as f:
        f.write(response.text)

# Function to extract ticket ID from response
def extract_ticket_id():
    with open('response.json', 'r') as f:
        response = json.load(f)
    return response.get('ticket', {}).get('id', '')

# Function to fetch Slack User ID by email
def get_slack_user_id(email):
    SLACK_API_TOKEN = _get_or_raise_env_var('SLACK_API_TOKEN')
    url = "https://slack.com/api/users.lookupByEmail"
    headers = {
        "Authorization": f"Bearer {SLACK_API_TOKEN}"
    }
    params = {
        "email": email
    }
    response = requests.get(url, headers=headers, params=params)
    user_id = response.json().get('user', {}).get('id', '')
    return user_id if user_id != "null" else ""

def send_slack_message(channel, message):
    SLACK_API_TOKEN = _get_or_raise_env_var("SLACK_API_TOKEN")
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SLACK_API_TOKEN}"
    }
    payload = {
        "channel": channel,
        "text": message
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()

def main():
    parser = argparse.ArgumentParser(description="Process incident details.")
    parser.add_argument('--description', required=True, help='The description of the incident')
    parser.add_argument('--servicename', required=True, help='The name of the service affected by the incident')
    parser.add_argument('--title', required=True, help='The title of the incident')
    parser.add_argument('--incident_url', required=True, help='The URL of the PagerDuty incident')
    parser.add_argument('--slackincidentcommander', required=True, help='The Slack ID of the incident commander')
    parser.add_argument('--slackdetectionmethod', required=True, help='The method used to detect the incident')
    parser.add_argument('--slackbusinessimpact', required=True, help='The business impact of the incident in Slack')
    parser.add_argument('--incident_id', required=True, help='The ID of the incident')
    parser.add_argument('--bridge_url', required=True, help='The URL for the incident bridge')
    parser.add_argument('--reporter_email', required=True, help='The email of the reporter')

    args = parser.parse_args()

    # Fetch Slack User ID for the reporter
    reporter_user_id = get_slack_user_id(args.reporter_email)

    # Create service ticket
    create_ticket(args.description, args.servicename, args.title, args.incident_url, args.slackincidentcommander, args.slackdetectionmethod, args.slackbusinessimpact, args.incident_id)

    # Extract ticket ID
    TICKET_ID = extract_ticket_id()

    # Generate ticket URL
    TICKET_URL = f"https://aenetworks.freshservice.com/a/tickets/{TICKET_ID}"

    # Slack channel ID for #incident_response
    channel_id = "CAZ6ZGBJ7"  # Replace with the actual channel ID for #incident_response

    # Generate the Slack message with channel and reporter tagging
    reporter_tag = f"<@{reporter_user_id}>" if reporter_user_id else args.reporter_email

    MESSAGE = f"""
    ************** SEV 1 ****************
    <@U04JCDSHS76> <@U04J2MTMRFD> <@U04FZPQSY3H> <@U048QRBV2NA> <@U04UKPX585S> <@U02SSCGCQQ6>
    Incident Commander: {args.slackincidentcommander}
    Detection Method: {args.slackdetectionmethod}
    Business Impact: {args.slackbusinessimpact}
    Bridge Link: <{args.bridge_url}|Bridge Link>
    Pagerduty Incident URL: {args.incident_url}
    FS Ticket URL: {TICKET_URL}
    Reported by: {reporter_tag}
    We will keep everyone posted on this channel as we assess the issue further.
    """

    # Send the message to the Slack channel using the Slack API
    send_slack_message(channel_id, MESSAGE)

if __name__ == "__main__":
    main()
