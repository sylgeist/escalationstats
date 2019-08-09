import slackClient from slack


def slackconnect(slacktoken):
    try:
        sc = slack.WebClient(slacktoken, timeout=90)
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
          'U08SNDXBN': 'nharasym',
          'U055571G9': 'afoster',
          'UB4V03GGG': 'akhan',
          'U04RPUJLH': 'cblake',
          'U6RCW3R0R': 'mfuller',
          'U027BHN6C': 'kd',
          'UCMH5BGCS': 'dhalperovich',
          'U02UB5H07': 'ncole',
          'UBP7DD7AB': 'mbrewka',
          'U02G9QH7Y': 'psingh',
          'U7SC0CB1P': 'rbennett'
          }
