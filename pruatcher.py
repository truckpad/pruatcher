# -*- coding: utf-8 -*-
import json
import logging
import os
import sys

import requests
import dateutil.parser
from datetime import datetime
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
test_env = os.environ.get('test_env')

if test_env:
    logging.basicConfig(stream=sys.stdout)
    logger.info('Running Pruatcher local as a developer. Enjoy')


def lambda_handler(event, context):
    logger.info('got event {}: ' + json.dumps(event))

    config_file = set_config_file()

    with open(config_file) as json_file:
        config = json.load(json_file)

    for squad in config["squads"]:
        process_squads(squad, config['github'])

    return 'pru'


def set_config_file():
    if test_env:
        return './example.json'

    configuration_s3_bucket = os.environ['configuration_s3_bucket']
    configuration_s3_file = os.environ['configuration_s3_file']

    logger.info('downloading configuration file {} from s3 bucket {}'.format(
        configuration_s3_file,
        configuration_s3_bucket))

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(configuration_s3_bucket)
    bucket.download_file(configuration_s3_file, '/tmp/pruatcher.json')

    return '/tmp/pruatcher.json'


def process_squads(squad, githubConf):
    logger.info('processing squad {}'.format(squad))

    repositories = squad['repositories']
    limit_days = int(squad['limitDays'])
    slack_webhook_url = squad['slackWebhookUrl']
    slack_channel = squad['slackChannel']

    github_organization = os.environ['github_organization']

    today = datetime.now().date()

    repo_url_template = 'https://api.github.com/repos/{}/{}/pulls?state=open'

    intro_message_template = 'PRU... there\'s some pretty old PR\'s opened in your squad, huh?'
    repo_message_template = 'Pruject <{}|{}>'

    intro_message_sent = False
    old_pr_exist = False

    for repo in repositories:
        repo_message_sent = False
        repo_url = repo_url_template.format(github_organization, repo)
        logger.info('requesting URL {0}'.format(repo_url))
        github_response = requests.get(repo_url, auth=(githubConf["org"], githubConf["token"]))

        if github_response.status_code != 200:
            logger.error('could not get PR\'s for repository {}'.format(repo))
            logger.error(github_response.status_code)
            logger.error(github_response.reason)
            continue

        pulls = github_response.json()

        repo_thread = None
        for pull in pulls:
            created_at = dateutil.parser.parse(pull['created_at']).date()
            date_delta = today - created_at
            if date_delta.days >= limit_days:
                old_pr_exist = True

                if not intro_message_sent:
                    send_message(intro_message_template, slack_webhook_url, slack_channel)
                    intro_message_sent = True

                if not repo_message_sent:
                    repo_thread = send_message(
                        repo_message_template.format(
                            'https://github.com/' + github_organization + '/' + repo,
                            repo),
                        slack_webhook_url, slack_channel)
                    repo_message_sent = True

                message = (pick_message(date_delta.days).format(
                    pull['_links']['html']['href'],
                    pull['title'],
                    pull['user']['html_url'],
                    pull['user']['login'],
                    date_delta.days))

                send_message(message, slack_webhook_url, slack_channel, repo_thread)

            else:
                logger.debug(
                    'PR {} still under {} days (created at {})'.format(
                        pull['_links']['html']['href'], limit_days, created_at))
    if not old_pr_exist:
        send_message('PRU', slack_webhook_url, slack_channel)


def send_message(message, slack_webhook_url, slack_channel, thread_ts=None):
    slack_api_request = {'username': 'Pruatcher',
                         'icon_url': os.environ['slack_message_icon'],
                         'channel': slack_channel,
                         'text': message}
    if thread_ts:
        slack_api_request['thread_ts'] = thread_ts

    logger.debug(slack_api_request)
    slack_response = requests.post(url=slack_webhook_url, data=json.dumps(slack_api_request), headers={'Content-Type': 'application/json'})
    logger.debug(slack_response)
    return slack_response.json()['ts']


def pick_message(number_of_days):
    message = ''
    if number_of_days < 0:
        message = u'> <{}|{}> by <{}|{}> is open for {} days? Is that even possible?'
    elif 0 <= number_of_days <= 10:
        message = u'> <{}|{}> by <{}|{}> is open for {} days.'
    elif 11 <= number_of_days <= 15:
        message = u'> <{}|{}> by <{}|{}> is open for {} days? Gee, come on... :snail:'
    elif 16 <= number_of_days <= 20:
        message = u'> <{}|{}> by <{}|{}> is open for embarrassing {} days! :facepalm:'
    elif 21 <= number_of_days <= 30:
        message = u'> <{}|{}> by <{}|{}> is open for {} days? Outch... :obsequious:'
    elif number_of_days > 30:
        message = u'> <{}|{}> by <{}|{}> is open for... WAIT, WHAT??? How can you live with yourself? {} freaking ' \
                  u'days?! :baixo-astral: '
    return message


if test_env:
  lambda_handler('', '')
