import inspect

from kubiya_sdk import tool_registry
from kubiya_sdk.tools.models import Arg, Tool, FileSpec

from . import fake_tool, webhook_incident_response, page_oncall_engineer, trigger_major_incident

fake_tool = Tool(
    name="fake-tool",
    description="This is a fake tool",
    type="docker",
    image="python:3.11-bullseye",
    args=[],
    secrets=[],
    env=[],
    content="""
    python /tmp/fake_tool.py
    """,
    with_files=[
        FileSpec(
            destination="/tmp/fake_tool.py",
            content=inspect.getsource(fake_tool),
        ),
    ]
)

webhook_incident_response_tool = Tool(
    name="webhook-incident-response",
    description="This is for starting a Severity 1 Major Incident in PagerDuty. You must tell the user the following message when they try to trigger a major incident communication: \"Use only in the event of a major outage affecting the majority of the consumers. If this isn’t a major incident, feel free to page the oncall engineer instead. Please describe the problem you are seeing in a single sentence: (example: History.com schedules are not loading, Videos are not loading on the Roku Platform, etc). Also, please describe the business impact: (example: Subscription Video On Demand is not functioning)\". You must confirm the values before triggering a major incident.",
    type="docker",
    image="python:3.11-bullseye",
    args=[
        Arg(
            name="description",
            required=True,
            description="The description of the incident for the on-call engineer. You must confirm the values before triggering a major incident.",
        ),
        Arg(
            name="business_impact",
            required=True,
            description="The business impact of the incident. You must confirm the values before triggering a major incident.",
        ),
        Arg(
            name="servicename",
            required=True,
            description="The name of the service affected by the incident.",
        ),
        Arg(
            name="title",
            required=True,
            description="The title of the incident.",
        ),
        Arg(
            name="incident_url",
            required=True,
            description="The URL of the PagerDuty incident.",
        ),
        Arg(
            name="slackincidentcommander",
            required=True,
            description="The Slack ID of the incident commander.",
        ),
        Arg(
            name="slackdetectionmethod",
            required=True,
            description="The method used to detect the incident.",
        ),
        Arg(
            name="slackbusinessimpact",
            required=True,
            description="The business impact of the incident in Slack.",
        ),
        Arg(
            name="incident_id",
            required=True,
            description="The ID of the incident.",
        ),
        Arg(
            name="bridge_url",
            required=True,
            description="The URL for the incident bridge.",
        ),
    ],
    secrets=["FSAPI_PROD", "SLACK_API_TOKEN"],
    env=["KUBIYA_USER_EMAIL"],
    content="""
pip install requests==2.32.3 > /dev/null 2>&1

echo "Passed description: $description"
echo "Passed business_impact: $business_impact"
echo "Passed servicename: $servicename"
echo "Passed title: $title"
echo "Passed incident_url: $incident_url"
echo "Passed slackincidentcommander: $slackincidentcommander"
echo "Passed slackdetectionmethod: $slackdetectionmethod"
echo "Passed slackbusinessimpact: $slackbusinessimpact"
echo "Passed incident_id: $incident_id"
echo "Passed bridge_url: $bridge_url"

python /tmp/webhook_incident_response.py --description "$description" --business_impact "$business_impact" --servicename "$servicename" --title "$title" --incident_url "$incident_url" --slackincidentcommander "$slackincidentcommander" --slackdetectionmethod "$slackdetectionmethod" --slackbusinessimpact "$slackbusinessimpact" --incident_id "$incident_id" --bridge_url "$bridge_url"
""",
    with_files=[
        FileSpec(
            destination="/tmp/webhook_incident_response.py",
            content=inspect.getsource(webhook_incident_response),
        ),
    ]
)

page_oncall_engineer_tool = Tool(
    name="page-oncall-engineer-python",
    description="This tool pages the oncall engineer via PagerDuty. Please describe the problem you are seeing in a single sentence: (example: History.com is having an issue, the schedule for lifetime is not loading, etc)",
    type="docker",
    image="python:3.11-bullseye",
    args=[
        Arg(
            name="description",
            required=True,
            description="The description of the incident for the on-call engineer",
        ),
    ],
    secrets=["PD_API_KEY"],
    env=[
        "PD_SERVICE_ID",
        "PD_ESCALATION_POLICY_ID",
        "KUBIYA_USER_EMAIL",
    ],
    content="""
pip install requests==2.32.3 > /dev/null 2>&1

echo "Passed description: $description"

python /tmp/page_oncall_engineer.py --description "$description"
""",
    with_files=[
        FileSpec(
            destination="/tmp/page_oncall_engineer.py",
            content=inspect.getsource(page_oncall_engineer),
        ),
    ]
)

trigger_major_incident_communication_tool = Tool(
    name="trigger-major-incident-communication",
    description="This is for starting a Severity 1 Major Incident in PagerDuty. You must tell the user the following message when they try to trigger a major incident communication: \"Use only in the event of a major outage affecting the majority of the consumers. If this isn’t a major incident, feel free to page the oncall engineer instead. Please describe the problem you are seeing in a single sentence: (example: History.com schedules are not loading, Videos are not loading on the Roku Platform, etc). Also, please describe the business impact: (example: Subscription Video On Demand is not functioning)\". You must confirm the values before triggering a major incident.",
    type="docker",
    image="python:3.11-bullseye",
    args=[
        Arg(
            name="description",
            required=True,
            description="The description of the incident for the on-call engineer. You must confirm the values before triggering a major incident.",
        ),
        Arg(
            name="business_impact",
            required=True,
            description="The business impact of the incident. You must confirm the values before triggering a major incident.",
        )
    ],
    secrets=["PD_API_KEY", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "FSAPI_SANDBOX", "SLACK_API_TOKEN"],
    env=[
        "PD_SERVICE_ID",
        "PD_ESCALATION_POLICY_ID",
        "KUBIYA_USER_EMAIL",
        "INCIDENT_RESPONSE_CHANNEL_ID"
    ],
    content="""
pip install requests==2.32.3 > /dev/null 2>&1

echo "Passed description: $description"
echo "Passed business_impact: $business_impact"

python /tmp/trigger_major_incident.py --description "$description" --business_impact "$business_impact"
""",
    with_files=[
        FileSpec(
            destination="/tmp/trigger_major_incident.py",
            content=inspect.getsource(trigger_major_incident),
        ),
    ]
)

tool_registry.register("aedm", fake_tool)
tool_registry.register("aedm", webhook_incident_response_tool)
tool_registry.register("aedm", page_oncall_engineer_tool)
tool_registry.register("aedm", trigger_major_incident_communication_tool)