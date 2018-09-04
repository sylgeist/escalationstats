import os
from slackclient import SlackClient
import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
sc = SlackClient(SLACK_API_TOKEN)

# Results storage
results = defaultdict(int)
user_researched = Counter()
user_resolved = Counter()
user_escalated = Counter()
user_rejected = Counter()


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


def userinfo(user_id):
    """Find friendly user name from Slack internal user ID"""
    user_req = sc.api_call(
        "users.info",
        user=user_id
    )
    if user_req['ok']:
        return user_req['user']['name']
    else:
        return user_req['error']


def esccount(messagelist):
    """Parse channel conversations and calculate stats from message reactions"""
    global user_researched, user_resolved, user_rejected, user_escalated

    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            for reaction in message['reactions']:
                if 'eyes' in reaction.values():
                    results['researched'] += 1
                    for user in reaction['users']:
                        user_researched[user] += 1
                elif 'white_check_mark' in reaction.values():
                    results['resolved'] += 1
                    for user in reaction['users']:
                        user_resolved[user] += 1
                elif 'hand' in reaction.values():
                    results['rejected'] += 1
                    for user in reaction['users']:
                        user_rejected[user] += 1
                elif 'jira' in reaction.values():
                    results['escalated'] += 1
                    for user in reaction['users']:
                        user_escalated[user] += 1


def userreport(header, userdict):
    """Helper function to print per user report substituting friendly user names for Slack ID"""
    print('\n' + header)
    if userdict:
        for k, v in userdict.items():
            print(f'{userinfo(k):12} => {v:3d} times')
    else:
        print("No occurrence during time frame.")


def find_channel(channel_alias):
    """Find Slack internal channel ID from friendly name"""
    channel_id = None
    channels = sc.api_call(
        "channels.list",
        exclude_archived=1
    )

    for channel in channels['channels']:
        if channel['name'] == channel_alias:
            channel_id = channel['id']

    if channel_id is None:
        raise Exception("cannot find channel " + channel_alias)

    return channel_id


def main():
    # Channel to pull stats from
    channel_name = 'escalations'
    channel_id = find_channel(channel_name)

    # Set up date range
    todaydate = datetime.datetime.today()
    enddate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    startdate_raw = enddate_raw - relativedelta(months=1)

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
    print(f'Escalations Researched:           {results["researched"]:>5}')
    print(f'Escalations Resolved by CloudOps: {results["resolved"]:>5}')
    print(f'Escalations Non-actionable:       {results["rejected"]:>5}')
    print(f'Escalated out of CloudOps:        {results["escalated"]:>5}')
    print(f'Total Escalations:                {sum(results.values()):>5}\n')

    print('Per User Breakdown:')
    userreport('Researched by:', user_researched)
    userreport('Resolved by:', user_resolved)
    userreport('Non-actionable by:', user_rejected)
    userreport('Escalated by:', user_escalated)


if __name__ == '__main__':
    main()
