import slack_sdk
import os
from pathlib import Path 
from dotenv import load_dotenv 
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env' 
load_dotenv(dotenv_path=env_path) 

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

BOT_TOKEN = os.environ['SLACK_TOKEN']
client = slack_sdk.WebClient(token=BOT_TOKEN) 
BOT_ID = client.api_call("auth.test")['user_id']

message_counts = {}
welcome_messages = {}

def ping(user_id):
    return "<@"+user_id+">"

class WelcomeMessage:
    START_TEXT = {
        'type':'section',
        'text':{
            'type':'mrkdwn',
            'text':(
                'Welcom to the channel \n\n'
                ' get start5ed by completing the taks'
            )
        }
    }
    DIVIDER = {'type':'divider'}



    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False
    def get_message(self):
        return{
            'ts': self.timestamp,
            'channel': self.channel,
            'username': 'Welcome robot!',
            'icon_emoji': self.icon_emoji,
            'blocks':[
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
    }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_square:'

        text = f'{checkmark} *react to this message*'

        return {'type':'section', 'text':{'type':'mrkdwn','text':text}}
    


@slack_event_adapter.on('reaction_added')
def reaction_added(payload):
    # print(payload)
    event = payload.get('event',{})
    emoji = event.get('reaction')
    user_id = event.get('user')
    channel_id = event.get('item')['channel']
    timestamp = event.get('item')['ts']
    if emoji =='x':
        if user_id == BOT_ID:
            client.chat_delete(channel=channel_id, ts=timestamp, as_user=False)

@app.route('/message-count', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id, 0)
    client.chat_postMessage(channel=channel_id, text= f"Message: {message_count}")
    return Response(), 200

def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel,user)
    message = welcome.get_message()
    print(message)
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome

@slack_event_adapter.on('message')
def message(payload):
    # print(payload)
    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        # client.chat_postMessage(channel=channel_id, text= ping(user_id)+" said: "+text)
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        if text.lower() == 'start':
            send_welcome_message(channel_id, user_id)


if __name__ == "__main__":
    app.run(debug=True)