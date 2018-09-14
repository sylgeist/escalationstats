import os
from slackclient import SlackClient
import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
sc = SlackClient(SLACK_API_TOKEN)

# Results storage
user_researched = Counter()
user_resolved = Counter()
user_escalated = Counter()
user_rejected = Counter()
followup = []

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
    permalink_req = sc.api_call(
        "chat.getPermalink",
        channel=channel,
        message_ts=message['ts']
    )

    if permalink_req['ok']:
        return permalink_req['permalink']
    else:
        return permalink_req['error']


def esccount(messagelist):
    """Parse channel conversations and calculate stats from message reactions"""
    global user_researched, user_resolved, user_rejected, user_escalated, followup

    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            for reaction in message['reactions']:
                if 'eyes' in reaction.values():
                    for user in reaction['users']:
                        user_researched[cloudopsteam[user]] += 1
                elif 'white_check_mark' in reaction.values():
                    for user in reaction['users']:
                        user_resolved[cloudopsteam[user]] += 1
                elif 'hand' in reaction.values():
                    for user in reaction['users']:
                        user_rejected[cloudopsteam[user]] += 1
                        followup.append([cloudopsteam[user], message['ts'], permalink(message, channel_id)])
                elif 'jira' in reaction.values():
                    for user in reaction['users']:
                        user_escalated[cloudopsteam[user]] += 1


def main():
    # Set up date range
    todaydate = datetime.datetime.today()
    # enddate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # startdate_raw = enddate_raw - relativedelta(months=1)
    startdate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    enddate_raw = datetime.datetime.today()

    # Convert to Slack friendly timestamp format
    enddate = enddate_raw.timestamp()
    startdate = startdate_raw.timestamp()

    # Pull channel history
    cursor = ''
    paginate = True
    while paginate:
        messageraw = sc.api_call(
            "conversations.history",
            channel=channel_id,
            inclusive=True,
            latest=enddate,
            oldest=startdate,
            cursor=cursor
        )
        esccount(messageraw)
        try:
            cursor = messageraw['response_metadata']['next_cursor']
        except KeyError:
            paginate = False

    # Generate report
    print(f'\nStart Date {startdate_raw} => {enddate_raw}\n')

    print(f'Total Events Received:     {sum(user_researched.values()):>3}\n')

    print(f'Resolved by CloudOps:      {sum(user_resolved.values()):>3} '
          f'({sum(user_resolved.values())/sum(user_researched.values()):.1%})')

    print(f'Non-actionable:            {sum(user_rejected.values()):>3} '
          f'({sum(user_rejected.values())/sum(user_researched.values()):.1%})')

    print(f'Escalated out of CloudOps: {sum(user_escalated.values()):>3} '
          f'({sum(user_escalated.values())/sum(user_researched.values()):.1%})')

    print(f'Incomplete escalations:    '
          f'{sum(user_researched.values())-sum(user_resolved.values())-sum(user_rejected.values())-sum(user_escalated.values()):>3}')

    for user in sorted(cloudopsteam.values()):
        print(f'\nUser stats for {user} ({user_researched[user]} Total Events):')
        if user_resolved[user]:
            print(f'Resolved:   {user_resolved[user]:>3} ({user_resolved[user]/user_researched[user]:.1%})')
        if user_rejected[user]:
            print(f'Rejected:   {user_rejected[user]:>3} ({user_rejected[user]/user_researched[user]:.1%})')
        if user_escalated[user]:
            print(f'Escalated:  {user_escalated[user]:>3} ({user_escalated[user]/user_researched[user]:.1%})')
        total = (user_escalated[user] + user_rejected[user] + user_resolved[user])
        if total < user_researched[user]:
            total = user_researched[user] - total
            print(f'Incomplete: {total:>3} ({total/user_researched[user]:.1%})')
        if (user_resolved[user] + user_rejected[user] + user_escalated[user]) > user_researched[user]:
            print('Inconsistent data: review for accuracy!')

    print('\nFollowup Items: (most recent first)')
    for user, timestamp, link in followup:
        print(f'Flagging User: {user}\n'
              f'Timestamp: {datetime.datetime.fromtimestamp(int(float(timestamp))).isoformat()}\n'
              f'Link: {link}')


if __name__ == '__main__':
    main()
