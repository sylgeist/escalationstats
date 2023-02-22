from slack import WebClient


def slackconnect(slacktoken):
    try:
        sc = WebClient(slacktoken, timeout=90)
    except Exception as err:
        print('Slack API Client Error:', str(err))
        exit(1)
    else:
        return sc


def permalink(sc, channel, message):
    """Create URL message link from internal Slack message ID"""
    permalink_req = sc.chat_getPermalink(
        channel=channel,
        message_ts=message['ts']
    )

    if permalink_req['ok']:
        return permalink_req['permalink']
    else:
        return permalink_req['error']


def channelhistory(sc, channel_id, startdate, enddate):
    # Convert to Slack friendly timestamp format
    end_timestamp = str(enddate.timestamp())
    start_timestamp = str(startdate.timestamp())

    # Pull channel history
    try:
        messageraw = sc.conversations_history(
            channel=channel_id,
            inclusive='true',
            latest=end_timestamp,
            oldest=start_timestamp,
        )
    except Exception as err:
        print('Slack API Error pulling conversation history', str(err))
        exit(1)
    else:
        return messageraw


cloudopsteam = {
          'UXXXXXXXX': 'name1',
          'UXXXXXXXX': 'name2',
          'UXXXXXXXX': 'name3',
          'UXXXXXXXX': 'name4',
          'UXXXXXXXX': 'name5',
          'UXXXXXXXX': 'name6',
          'UXXXXXXXX': 'name7',
          'UXXXXXXXX': 'name8',
          'UXXXXXXXX': 'name9',
          'UXXXXXXXX': 'name10',
          'UXXXXXXXX': 'name11',
          'UXXXXXXXX': 'name12'
          }
