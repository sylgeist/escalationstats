from dateutil.relativedelta import relativedelta
import datetime
import statistics
import escalations
import os


channel_id = 'C024HPA08'  # escalations channel ID
cloudopsteam = escalations.cloudopsteam  # cloudops team to slack ID mapping
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')  # slack token in ENV variable
sc = escalations.slackconnect(SLACK_API_TOKEN)

dhalperovich = []
afoster = []
nharasym = []


def escalationmetrics(messagelist, response_metrics):
    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            for reaction in message['reactions']:
                if 'eyes' in reaction['name']:
                    for user in reaction['users']:
                        if user in cloudopsteam:
                            if 'replies' in message.keys():
                                for reply in message['replies']:
                                    if reply['user'] in cloudopsteam:
                                        start = datetime.datetime.fromtimestamp(float(message['ts']))
                                        first_reply = datetime.datetime.fromtimestamp(float(reply['ts']))
                                        response_time = (first_reply - start).total_seconds()/60
                                        # more than 250 minutes indicates a forgotten escalation or comm failure
                                        if response_time < 500:
                                            response_metrics.append(response_time)
                                        if 50 < response_time < 43000:
                                            print("Time to first reply: %5.0f minutes User: %12s Link: %s" % (response_time, cloudopsteam[reply['user']], escalations.permalink(sc, channel_id, message)))
                                        break


def main():
    response_metrics = []



    # Set up date range
    enddate_raw = datetime.datetime.today()
    startdate_raw = enddate_raw - relativedelta(months=3)

    messagelist = escalations.channelhistory(sc, channel_id, startdate_raw, enddate_raw)

    for message in messagelist:
        escalationmetrics(message, response_metrics)

    print(f'Total escalations: {len(response_metrics):>5}\n'
          f'\tStd Deviation:     {statistics.pstdev(response_metrics):>5.2f} minutes\n'
          f'\tAvg (first reply): {statistics.mean(response_metrics):>5.2f} minutes\n'
          f'\t50th percentile:   {statistics.median_grouped(response_metrics):>5.2f} minutes\n')


if __name__ == '__main__':
    main()
