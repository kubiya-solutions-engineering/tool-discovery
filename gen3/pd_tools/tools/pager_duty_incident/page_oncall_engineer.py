#!/usr/bin/env python3

import os
import requests
import argparse

def _get_or_raise_env_var(env_var):
    value = os.getenv(env_var)
    if value is None:
        raise Exception(f"Env var {env_var} is not set")
    return value

def create_pd_incident(description: str):
    PD_API_KEY = _get_or_raise_env_var("PD_API_KEY")
    SERVICE_ID = _get_or_raise_env_var("PD_SERVICE_ID")
    ESCALATION_POLICY_ID = _get_or_raise_env_var("PD_ESCALATION_POLICY_ID")
    KUBIYA_USER_EMAIL = _get_or_raise_env_var("KUBIYA_USER_EMAIL")

    url = "https://api.pagerduty.com/incidents"
    headers = {
        "Authorization": f"Token token={PD_API_KEY}",
        "Content-Type": "application/json",
        "From": KUBIYA_USER_EMAIL,
    }
    payload = {
        "incident": {
            "type": "incident",
            "title": f"Assistance requested via Kubi - {description}",
            "service": {"id": SERVICE_ID, "type": "service_reference"},
            "escalation_policy": {
                "id": ESCALATION_POLICY_ID,
                "type": "escalation_policy_reference",
            },
            "body": {"type": "incident_body", "details": description},
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Failed to create incident: {e}")

    try:
        return response.json()["incident"]["id"]
    except Exception as e:
        raise Exception(f"Failed to fetch incident id: {e}")

def main():
    parser = argparse.ArgumentParser(description="Page the on-call engineer via PagerDuty.")
    parser.add_argument('--description', required=True, help='The description of the incident for the on-call engineer')
    args = parser.parse_args()

    pd_incident_id = create_pd_incident(args.description)
    print(
        f"The on-call engineer has been paged. They will reach out to you as soon as possible. Your PagerDuty incident URL is https://aetnd.pagerduty.com/incidents/{pd_incident_id}"
    )

if __name__ == "__main__":
    main()