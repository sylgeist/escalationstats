import os
from slackclient import SlackClient
import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')

try:
    sc = SlackClient(SLACK_API_TOKEN)
except Exception as err:
    print('Error:', str(err))
    exit(1)

# Results storage
user_researched = Counter()
user_resolved = Counter()
user_escalated = Counter()
user_rejected = Counter()
user_incomplete = Counter()
followup = []
incomplete = []

# escalations channel ID
channel_id = 'C024HPA08'

# slack to common name mapping
cloudopsteam = {
          'U08SNDXBN': 'nharasym',
          'U055571G9': 'afoster',
          'UB4V03GGG': 'akhan',
          'U04RPUJLH': 'cblake',
          'U02EU172H': 'cweeks',
          'U027BHN6C': 'kd',
          'UCMH5BGCS': 'dhalperovich',
          'U04V9S0JJ': 'genpage',
          'UBP7DD7AB': 'mbrewka',
          'U02G9QH7Y': 'psingh'
          }


def permalink(message, channel):
    """Create URL message link from internal Slack message ID"""
    try:
        permalink_req = sc.api_call(
            "chat.getPermalink",
            channel=channel,
            message_ts=message['ts']
        )
    except Exception as err:
        print('Error:', str(err))
        exit(1)
    else:
        if permalink_req['ok']:
            return permalink_req['permalink']
        else:
            return permalink_req['error']


def user_info(user_id):
    """Find friendly user name from Slack internal user ID"""
    try:
        user_req = sc.api_call(
            "users.info",
            user=user_id
        )
    except Exception as err:
        print('Error:', str(err))
        exit(1)
    else:
        if user_req['ok']:
            return user_req['user']['name']
        else:
            return user_req['error']


def esccount(messagelist):
    """Parse channel conversations and calculate stats from message reactions"""
    global user_researched, user_resolved, user_rejected, user_escalated, user_incomplete, followup, incomplete

    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            if any(reaction['name'] == 'eyes' for reaction in message['reactions']):
                for reaction in message['reactions']:
                    if 'eyes' in reaction['name']:
                        for user in reaction['users']:
                            if user in cloudopsteam:
                                user_researched[cloudopsteam[user]] += 1
                                if len(message['reactions']) == 1:
                                    user_incomplete[cloudopsteam[user]] += 1
                                    incomplete.append(
                                        [cloudopsteam[user], message['ts'], permalink(message, channel_id)])
                            else:
                                continue
                    elif 'white_check_mark' in reaction['name']:
                        for user in reaction['users']:
                            if user in cloudopsteam:
                                user_resolved[cloudopsteam[user]] += 1
                            else:
                                continue
                    elif 'hand' in reaction['name']:
                        for user in reaction['users']:
                            if user in cloudopsteam:
                                user_rejected[cloudopsteam[user]] += 1
                                followup.append([cloudopsteam[user], message['ts'], permalink(message, channel_id)])
                            else:
                                continue
                    elif 'jira' in reaction['name']:
                        for user in reaction['users']:
                            if user in cloudopsteam:
                                user_escalated[cloudopsteam[user]] += 1
                            else:
                                continue


def main():
    # Set up date range
    todaydate = datetime.datetime.today()
    enddate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    startdate_raw = enddate_raw - relativedelta(months=1)
    # startdate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # enddate_raw = datetime.datetime.today()

    # Convert to Slack friendly timestamp format
    enddate = enddate_raw.timestamp()
    startdate = startdate_raw.timestamp()

    # Pull channel history
    cursor = ''
    paginate = True
    while paginate:
        try:
            messageraw = sc.api_call(
                "conversations.history",
                channel=channel_id,
                inclusive=True,
                latest=enddate,
                oldest=startdate,
                cursor=cursor
            )
        except Exception as err:
            print('Error:', str(err))
            exit(1)
        else:
            # TODO check for auth errors in http response
            esccount(messageraw)

        try:
            cursor = messageraw['response_metadata']['next_cursor']
        except KeyError:
            paginate = False

    # Generate report
    print(f'\nEscalation Stats for: {startdate_raw.strftime("%B")} {startdate_raw.year}\n')

    print(f'Total Events Received:     {sum(user_researched.values()):>3}\n')

    print(f'Resolved by CloudOps:      {sum(user_resolved.values()):>3} '
          f'({sum(user_resolved.values())/sum(user_researched.values()):.1%})')

    print(f'Non-actionable:            {sum(user_rejected.values()):>3} '
          f'({sum(user_rejected.values())/sum(user_researched.values()):.1%})')

    print(f'Escalated out of CloudOps: {sum(user_escalated.values()):>3} '
          f'({sum(user_escalated.values())/sum(user_researched.values()):.1%})')

    print(f'Incomplete escalations:    {sum(user_incomplete.values()):>3} '
          f'({sum(user_incomplete.values())/sum(user_researched.values()):.1%})')

    for user in sorted(cloudopsteam.values()):
        print(f'\nUser stats for {user} ({user_researched[user]} Total Events):')
        if user_resolved[user]:
            print(f'Resolved:   {user_resolved[user]:>3} ({user_resolved[user]/user_researched[user]:.1%})')
        if user_rejected[user]:
            print(f'Rejected:   {user_rejected[user]:>3} ({user_rejected[user]/user_researched[user]:.1%})')
        if user_escalated[user]:
            print(f'Escalated:  {user_escalated[user]:>3} ({user_escalated[user]/user_researched[user]:.1%})')
        if user_incomplete[user]:
            print(f'Incomplete: {user_incomplete[user]:>3} ({user_incomplete[user]/user_researched[user]:.1%})')
        if (user_resolved[user] + user_rejected[user] + user_escalated[user]) > user_researched[user]:
            print('Inconsistent data: review for accuracy!')

    print('\nFollowup Items: (most recent first)')
    for user, timestamp, link in followup:
        print(f'Flagging User: {user}\n'
              f'Timestamp: {datetime.datetime.fromtimestamp(int(float(timestamp))).isoformat()}\n'
              f'Link: {link}')

    print('\nIncomplete Items: (most recent first)')
    for user, timestamp, link in incomplete:
        print(f'Starting User: {user}\n'
              f'Timestamp: {datetime.datetime.fromtimestamp(int(float(timestamp))).isoformat()}\n'
              f'Link: {link}')

if __name__ == '__main__':
    main()
