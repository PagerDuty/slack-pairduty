import os
import time
import random
from slackclient import SlackClient


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_commands(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command == "help":
        response = "Hey there! :wave: PDMeetup helps to encourage Dutonians who don't know each other well to meet for coffee, lunch, or just to chat! :panda-dance: \n\n If @pdmeetup is invited to a channel, it will pair the channel's members via direct message every week. You can also chat @pdmeetup when you want to meet someone new."

    elif command == "meetup":
        channel_api_call = slack_client.api_call("channels.info", channel=channel)

        if channel_api_call.get('ok'):
            # retrieve all the members in current channel
            all_members = channel_api_call['channel'].get('members')
            channel_users = []
            print(channel_api_call.get('name'))
            print(all_members)
            for member in all_members:
                bot_check = slack_client.api_call("bots.info", bot=member)
                print(bot_check)
                if bot_check.get('error') == 'bot_not_found' and member != user:
                    channel_users.append(member)

            user_count = len(channel_users) - 1
            print(user_count)
        buddy = channel_users[random.randint(0,user_count)]
        buddy_api_call = slack_client.api_call("users.info", user=buddy)
        user_api_call = slack_client.api_call("users.info", user=user)
        user_message = "\n\
\
*Hello!* :partyparrot: I'm your friendly PDMeetup bot, here to encourage you to get to know your fellow Dutonians by pairing people from %s.\n\n\
Today, why not send <@%s> a message and schedule lunch or coffee with them?\n\n\
If you don't want to receive future pairings, feel free to leave the channel %s.\
" % (channel_api_call['channel'].get('name'),buddy_api_call['user'].get('name'),channel_api_call['channel'].get('name'))

        slack_client.api_call("chat.postMessage", channel = user, text = user_message, as_user = True)

    else:
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    print(output_list)
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), output['channel'], output['user']
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("PairDutyTest connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_commands(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
