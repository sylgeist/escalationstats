import os
import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter
import escalations

channel_id = 'C024HPA08'  # escalations channel ID
cloudopsteam = escalations.cloudopsteam  # cloudops team to slack ID mapping
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')  # slack token in ENV variable
sc = escalations.slackconnect(SLACK_API_TOKEN)

# Results storage
user_researched = Counter()
user_resolved = Counter()
user_escalated = Counter()
user_rejected = Counter()
user_incomplete = Counter()
followup = []
incomplete = []


def esccount(messagelist):
    """Parse channel conversations and calculate stats from message reactions"""
    global user_researched, user_resolved, user_rejected, user_escalated, user_incomplete, followup, incomplete

    # Iterate through the list looking for reactions and users of interest
    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            for reaction in message['reactions']:
                if 'eyes' in reaction['name']:
                    for user in reaction['users']:
                        if user in cloudopsteam:
                            user_researched[cloudopsteam[user]] += 1
                            if len(message['reactions']) == 1:
                                user_incomplete[cloudopsteam[user]] += 1
                                incomplete.append(
                                    [cloudopsteam[user], message['ts'], escalations.permalink(sc, channel_id, message)])
                elif 'white_check_mark' in reaction['name']:
                    for user in reaction['users']:
                        if user in cloudopsteam:
                            user_resolved[cloudopsteam[user]] += 1
                elif 'hand' in reaction['name']:
                    for user in reaction['users']:
                        if user in cloudopsteam:
                            user_rejected[cloudopsteam[user]] += 1
                            followup.append(
                                [cloudopsteam[user], message['ts'], escalations.permalink(sc, channel_id, message)])
                elif 'jira' in reaction['name']:
                    for user in reaction['users']:
                        if user in cloudopsteam:
                            user_escalated[cloudopsteam[user]] += 1


def main():
    # Set up date range
    todaydate = datetime.datetime.today()
    enddate_raw = todaydate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    startdate_raw = enddate_raw - relativedelta(months=1)

    # pull the message history from Slack
    for messagebatch in escalations.channelhistory(sc, channel_id, startdate_raw, enddate_raw):
        # print(message['has_more'])
        esccount(messagebatch)

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
        print(f'\nUser: {user} stats ({user_researched[user]} Total Events):')
        if user_resolved[user]:
            print(f'\tResolved:   {user_resolved[user]:>3} ({user_resolved[user]/user_researched[user]:.1%})')
        if user_rejected[user]:
            print(f'\tRejected:   {user_rejected[user]:>3} ({user_rejected[user]/user_researched[user]:.1%})')
        if user_escalated[user]:
            print(f'\tEscalated:  {user_escalated[user]:>3} ({user_escalated[user]/user_researched[user]:.1%})')
        if user_incomplete[user]:
            print(f'\tIncomplete: {user_incomplete[user]:>3} ({user_incomplete[user]/user_researched[user]:.1%})')
        if (user_resolved[user] + user_rejected[user] + user_escalated[user]) > user_researched[user]:
            print('\tInconsistent data: review for accuracy!')


    print('\nFollowup Items: (most recent first)')
    for user, timestamp, link in followup:
        print(f'\tUser: {user}\n'
              f'\tTimestamp: {datetime.datetime.fromtimestamp(int(float(timestamp))).isoformat()}\n'
              f'\tLink: {link}')

    print('\nIncomplete Items: (most recent first)')
    for user, timestamp, link in incomplete:
        print(f'\tUser: {user}\n'
              f'\tTimestamp: {datetime.datetime.fromtimestamp(int(float(timestamp))).isoformat()}\n'
              f'\tLink: {link}')


if __name__ == '__main__':
    main()
