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
    change_time = message['StateChangeTime'].split("+")

    #KST 시간 변환
    kst_time = datetime.strptime(change_time[0], '%Y-%m-%dT%H:%M:%S.%f') - timedelta(hours=-9)

#    slack_message = {
#        'channel': SLACK_CHANNEL,
#        'text': "%s state is now %s: %s" % (alarm_name, new_state, reason)
#    }

    color = "#30db3f" if alarm_name.find("off") >= 0 else "#eb4034"

    slack_message = {
        "channel": SLACK_CHANNEL,
        "attachments": [{
            "color": color,
            "blocks": [{
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*Task:*\\n" + alarm_description
                },
                {
                    "type": "mrkdwn",
                    "text": "*경보 시간:*\\n" + str(kst_time)
                }]
            }]
        }],
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": alarm_name
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