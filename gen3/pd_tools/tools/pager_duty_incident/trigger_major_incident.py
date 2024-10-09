#!/usr/bin/env python3

import os
import requests
import json
import argparse
from datetime import datetime, time, timedelta

def _get_or_raise_env_var(env_var):
    value = os.getenv(env_var)
    if value is None:
        raise Exception(f"Env var {env_var} is not set")
    return value

def get_access_token():
    AZURE_TENANT_ID = _get_or_raise_env_var("AZURE_TENANT_ID")
    AZURE_CLIENT_ID = _get_or_raise_env_var("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET = _get_or_raise_env_var("AZURE_CLIENT_SECRET")
    
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "client_id": AZURE_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": AZURE_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def get_oncall_engineer(escalation_policy_id):
    PD_API_KEY = _get_or_raise_env_var("PD_API_KEY")
    GET_ONCALL_ENGINEER_POLICY_ID = "PG2K3KC"
    
    url = f"https://api.pagerduty.com/oncalls?escalation_policy_ids[]={GET_ONCALL_ENGINEER_POLICY_ID}"
    headers = {
        "Authorization": f"Token token={PD_API_KEY}",
        "Accept": "application/vnd.pagerduty+json;version=2"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    oncalls = response.json().get("oncalls", [])
    for oncall in oncalls:
        if oncall.get("user"):
            return oncall["user"]["summary"]
    return "Incident Commander"

def create_pd_incident(description):
    PD_API_KEY = _get_or_raise_env_var("PD_API_KEY")
    KUBIYA_USER_EMAIL = _get_or_raise_env_var("KUBIYA_USER_EMAIL")
    SERVICE_ID = _get_or_raise_env_var("PD_SERVICE_ID")
    ESCALATION_POLICY_ID = _get_or_raise_env_var("PD_ESCALATION_POLICY_ID")
    FSAPI_PROD = os.getenv("FSAPI_PROD")
    FSAPI_SANDBOX = os.getenv("FSAPI_SANDBOX")
    
    url = "https://api.pagerduty.com/incidents"
    headers = {
        "Authorization": f"Token token={PD_API_KEY}",
        "Content-Type": "application/json",
        "From": KUBIYA_USER_EMAIL
    }
    if FSAPI_PROD:
        title_prefix = "Major Incident via Kubi - "
    elif FSAPI_SANDBOX:
        title_prefix = "TEST TICKET.IGNORE.Major Incident via Kubi - "
    else:
        raise Exception("Neither FSAPI_PROD nor FSAPI_SANDBOX is set")
    
    payload = {
        "incident": {
            "type": "incident",
            "title": f"{title_prefix}{description}",
            "service": {
                "id": SERVICE_ID,
                "type": "service_reference"
            },
            "escalation_policy": {
                "id": ESCALATION_POLICY_ID,
                "type": "escalation_policy_reference"
            },
            "body": {
                "type": "incident_body",
                "details": description
            }
        }
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {headers}")
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    response.raise_for_status()
    return response.json()["incident"]["id"]

def close_pd_incident(pd_incident_id):
    KUBIYA_USER_EMAIL = _get_or_raise_env_var("KUBIYA_USER_EMAIL")
    PD_API_KEY = _get_or_raise_env_var("PD_API_KEY")

    url = f"https://api.pagerduty.com/incidents/{pd_incident_id}"
    headers = {
        "Authorization": f"Token token={PD_API_KEY}",
        "Content-Type": "application/json",
        "From": KUBIYA_USER_EMAIL
    }
    payload = {
        "incident": {
            "type": "incident",
            "status": "resolved"
        }
    }
    print(f"Closing Incident with ID: {pd_incident_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {headers}")
    response = requests.put(url, headers=headers, data=json.dumps(payload))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    response.raise_for_status()
    return response.json()["incident"]["id"]  

def create_ticket(description, business_impact, incident_id, incident_commander):
    KUBIYA_USER_EMAIL = _get_or_raise_env_var("KUBIYA_USER_EMAIL")
    FSAPI_PROD = os.getenv("FSAPI_PROD")
    FSAPI_SANDBOX = os.getenv("FSAPI_SANDBOX")
    FSAPI = FSAPI_PROD if FSAPI_PROD else FSAPI_SANDBOX
    
    if not FSAPI:
        raise Exception("Neither FSAPI_PROD nor FSAPI_SANDBOX is set")
    
    if FSAPI_PROD:
        url = "https://aenetworks.freshservice.com/api/v2/tickets"
        subject = f"MAJOR INCIDENT pagerduty-kubiya-page-oncall-service - Major Incident via Kubi"
    elif FSAPI_SANDBOX:
        url = "https://aenetworks-fs-sandbox.freshservice.com/api/v2/tickets"
        subject = f"TEST TICKET.IGNORE.MAJOR INCIDENT pagerduty-kubiya-page-oncall-service - Major Incident via Kubi"
    
    user_email = KUBIYA_USER_EMAIL
    payload = {
        "description": f"{description}<br><strong>Incident Commander:</strong> {incident_commander}<br><strong>Detection Method:</strong> Detection Method<br><strong>Business Impact:</strong> {business_impact}<br><strong>Ticket Link:</strong>PagerDuty Incident",
        "subject": subject,
        "email": user_email,
        "priority": 1,
        "status": 2,
        "source": 8,
        "category": "DevOps",
        "sub_category": "Pageout",
        "tags": [f"PDID_{incident_id}"]
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, auth=(FSAPI, "X"), data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["ticket"]["id"]

def close_ticket(ticket_id):
    FSAPI_PROD = os.getenv("FSAPI_PROD")
    FSAPI_SANDBOX = os.getenv("FSAPI_SANDBOX")
    FSAPI = FSAPI_PROD if FSAPI_PROD else FSAPI_SANDBOX

    if not FSAPI:
        raise Exception("Neither FSAPI_PROD nor FSAPI_SANDBOX is set")

    if FSAPI_PROD:
        url = f"https://aenetworks.freshservice.com/api/v2/tickets{ticket_id}"
    elif FSAPI_SANDBOX:   
        url = f"https://aenetworks-fs-sandbox.freshservice.com/api/v2/tickets{ticket_id}"

    payload = {
        "status": 4,    
        "Agents": 3,       
        "custom_fields": {
          "close_code": "No Action Taken",
          "resolution_notes": "Test ticket for kubiya. Hence resolving the ticket"  # You may need to adjust this value based on your allowed close codes
         }
    }

    response = requests.put(url, headers={"Content-Type": "application/json"}, auth=(FSAPI, "X"), data=json.dumps(payload))
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code == 200:
        try:
            return response.json()["ticket"]["id"]
        except json.JSONDecodeError:
            print("Failed to parse JSON response")
            return None
    else:
        print(f"Failed to update ticket {ticket_id}. Status code: {response.status_code}")
        return None

def create_meeting(access_token):
    url = "https://graph.microsoft.com/v1.0/users/d69debf1-af1f-493f-8837-35747e55ea0f/onlineMeetings"
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=1)
    payload = {
        "startDateTime": start_time.isoformat() + "Z",
        "endDateTime": end_time.isoformat() + "Z"
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["joinUrl"]

def get_slack_user_id(email):
    SLACK_API_TOKEN = _get_or_raise_env_var("SLACK_API_TOKEN")
    
    url = "https://slack.com/api/users.lookupByEmail"
    headers = {
        "Authorization": f"Bearer {SLACK_API_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {"email": email}
    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()

    if response_data["ok"]:
        return response_data["user"]["id"]
    else:
        print(f"Error fetching user ID for {email}: {response_data['error']}")
        return None

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
    parser = argparse.ArgumentParser(description="Trigger a major incident communication")
    parser.add_argument("--description", required=True, help="The description of the incident")
    parser.add_argument("--business_impact", required=True, help="The business impact of the incident")
    args = parser.parse_args()

    description = args.description
    business_impact = args.business_impact
        
    FSAPI_PROD = os.getenv("FSAPI_PROD")
    FSAPI_SANDBOX = os.getenv("FSAPI_SANDBOX")

    reporter = _get_or_raise_env_var("KUBIYA_USER_EMAIL")
    access_token = get_access_token()
    escalation_policy_id = _get_or_raise_env_var("PD_ESCALATION_POLICY_ID")
    incident_commander = get_oncall_engineer(escalation_policy_id)
    pd_incident_id = create_pd_incident(description)
    ticket_id = create_ticket(description, business_impact, pd_incident_id, incident_commander)

    if FSAPI_PROD:
        ticket_url = f"https://aenetworks.freshservice.com/a/tickets/{ticket_id}"
    elif FSAPI_SANDBOX:
        ticket_url = f"https://aenetworks-fs-sandbox.freshservice.com/a/tickets/{ticket_id}"

    meeting_link = create_meeting(access_token)
    
    # Fetch Slack user ID for the reporter
    print(f"Fetching Slack user ID for email: {reporter}")
    reporter_user_id = get_slack_user_id(reporter)
    reporter_mention = f"<@{reporter_user_id}>" if reporter_user_id else reporter

    # Channel ID for #incident_response (replace with actual ID)
    channel_id = _get_or_raise_env_var("INCIDENT_RESPONSE_CHANNEL_ID")

    if FSAPI_PROD:
        message = (
            "************** SEV 1 ****************\n"
            "<@U04JCDSHS76> <@U04J2MTMRFD> <@U04FZPQSY3H> <@U048QRBV2NA> <@U04UKPX585S> <@U02SSCGCQQ6>\n"
            f"Incident Commander: {incident_commander}\n"
            f"Description: {description}\n"
            f"Business Impact: {business_impact}\n"
            f"Bridge Link: <{meeting_link}|Bridge Link>\n"
            f"PagerDuty Incident URL: https://aetnd.pagerduty.com/incidents/{pd_incident_id}\n"
            f"FS Ticket URL: {ticket_url}\n"
            f"Reported by: {reporter_mention}\n"
            "We will keep everyone posted on this channel as we assess the issue further."
        )
    elif FSAPI_SANDBOX:
        message = (
            "************** THIS IS A TEST -- DISREGARD ****************\n"
            "@Jeff McGrath @Kevin Keeler @Tapan Shah @Neeraj Mendiratta @John Dispirito @Sebastian Marjanovic\n"
            f"Incident Commander: {incident_commander}\n"
            f"Description: {description}\n"
            f"Business Impact: {business_impact}\n"
            f"Bridge Link: <{meeting_link}|Bridge Link>\n"
            f"PagerDuty Incident URL: https://aetnd.pagerduty.com/incidents/{pd_incident_id}\n"
            f"FS Ticket URL: {ticket_url}\n"
            f"Reported by: {reporter_mention}\n"
            "We will keep everyone posted on this channel as we assess the issue further."
        )
    send_slack_message(channel_id, message.strip())

    channel_name = _get_or_raise_env_var("INCIDENT_RESPONSE_CHANNEL_NAME")
    print(f"Please go to the <#{channel_id}|{channel_name}> channel to find the SEV1 announcement. The bridge line and pertinent details have been posted there. Thank you.")
    
    if FSAPI_SANDBOX:
        time.sleep(60)
        close_pd_incident(pd_incident_id)
        close_ticket(ticket_id)
    else:
        print("This is a production environment, so we will not close the incident or ticket.")

if __name__ == "__main__":
    main()