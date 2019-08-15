from dateutil.relativedelta import relativedelta
import datetime
import statistics
import escalations
import os

channel_id = 'C024HPA08'  # escalations channel ID
cloudopsuser = 'UB4V03GGG'  # cloudops team to slack ID mapping
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')  # slack token in ENV variable
sc = escalations.slackconnect(SLACK_API_TOKEN)
esclist = []

def escalationmetrics(messagelist, response_metrics):
    for message in messagelist['messages']:
        if 'reactions' in message.keys():
            for reaction in message['reactions']:
                if 'eyes' in reaction['name'] and cloudopsuser in reaction['users']:
                    if 'replies' in message.keys():
                        for reply in message['replies']:
                            if reply['user'] == cloudopsuser:
                                start = datetime.datetime.fromtimestamp(float(message['ts']))
                                first_reply = datetime.datetime.fromtimestamp(float(reply['ts']))
                                # message_time = datetime.datetime.fromtimestamp(int(float(message['ts']))).isoformat()
                                response_time = (first_reply - start).total_seconds()/60
                                # esclist.append([response_time, message['reply_count'], message_time, permalink(message, channel_id)])
                                response_metrics.append(response_time)
                                if response_time > 15:
                                    print(f'Start: {start.strftime("%Y-%m-%d %H:%M:%S")} '
                                      f'First Reply: {first_reply.strftime("%Y-%m-%d %H:%M:%S")} '
                                      f'Replies: {message["reply_count"]} Response Time: {response_time:.1f}\n'
                                      f' Link: {escalations.permalink(sc, channel_id, message)}')
                                break


def main():
    response_metrics = []

    # Set up date range
    enddate_raw = datetime.datetime.today()
    startdate_raw = enddate_raw - relativedelta(months=2)

    messagelist = escalations.channelhistory(sc, channel_id, startdate_raw, enddate_raw)

    for message in messagelist:
        escalationmetrics(message, response_metrics)

    print('\nEscalations')
    for response, replies, timestamp, link in esclist:
         print(f'Response Time: {response} Replies: {replies} Timestamp: {timestamp.strftime("%Y-%m-%d %H:%M:%S")} Link: {link}')
    print(f'Total escalations:  {len(response_metrics):>5}\n'
          f'Standard Deviation: {statistics.stdev(response_metrics):>5.2f} minutes\n'
          f'Average:            {statistics.mean(response_metrics):>5.2f} minute to first reply\n'
          f'Grouped Average:    {statistics.median_grouped(response_metrics):>5.2f} minutes\n')

if __name__ == '__main__':
    main()
