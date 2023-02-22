import os
from slack import WebClient

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
try:
    sc = WebClient(SLACK_API_TOKEN)
except Exception as err:
    print('Error:', str(err))
    exit(1)

def user_info(user_id):
    """Find friendly user name from Slack internal user ID"""
    try:
        user_req = sc.users_info(
            user=user_id
        )
    except Exception as err:
        print("Error:", err)
        exit(1)
    else:
        return user_req['user']['name']


if __name__ == '__main__':
    name = input("What is the Slack userid?")
    print(user_info(name))
