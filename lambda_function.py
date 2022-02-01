import boto3
import json
import logging
import os

from base64 import b64decode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime
from datetime import timedelta

# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['slackChannel']
   
HOOK_URL = os.environ['hookUrl']

# 어드민 사이트 - BO
ADMIN_URL = 'https://127.0.0.1:8380'
# 웹 사이트 - FO
WEB_URL = 'https://127.0.0.1:8180'
# 모바일 사이트 - MO
MOBILE_URL = 'https://127.0.0.1:8280'   
   
logger = logging.getLogger()
logger.setLevel(logging.INFO)
   
def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))
   
    alarm_name = message['AlarmName']
    alarm_description = message['AlarmDescription']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']
    change_time = message['StateChangeTime'].split(".")

    #KST 시간 변환
    kst_time = datetime.strptime(change_time[0], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=-9)

    color = "#30db3f" if new_state.find("OK") >= 0 else "#eb4034"
    alarm_name = alarm_name + " UP" if new_state.find("OK") >= 0 else alarm_name + " DOWN"
    alarm_description = alarm_description + " up" if new_state.find("OK") >= 0 else alarm_description + " down"
    site_url = WEB_URL

    if alarm_name.find("BO") >= 0:
        site_url = ADMIN_URL
    elif alarm_name.find("MO") >= 0:
        site_url = MOBILE_URL

    slack_message = {
        "channel": SLACK_CHANNEL,
        "text": alarm_name,
        "attachments": [{
            "color": color,
            "blocks": [{
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*Task:*\n" + alarm_description
                },
                {
                    "type": "mrkdwn",
                    "text": "*Create Time:*\n" + str(kst_time)
                },
                {
                    "type": "mrkdwn",
                    "text": "*URL:*\n" + site_url
                }]
            }]
        }],
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*" + alarm_name + "*"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": reason
            }]
        }]
    }

    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)