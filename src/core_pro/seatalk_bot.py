"""
https://api.slack.com/incoming-webhooks
"""

import json
import requests


def seatalk_notification(group_id, text, mention_lst=None):
    webhook_url = group_id
    slack_data = {
        "tag": "text",
        "text": {
            "content": text,
            "mentioned_email_list": mention_lst,
            "at_all": False
        }
    }

    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
