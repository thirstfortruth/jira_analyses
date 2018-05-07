import requests
import json
import base64
import pandas as pd
import ijson
from datetime import datetime as dt
from dateutil.parser import parse


# JIRA_BASE_URL='https://jira.atlassian.com'
JIRA_BASE_URL = 'https://jira.global.tesco.org'
AUTH_STRING = b'USERNAME:PASSWORD'
ENC_AUTH_STRING = 'Basic ' + base64.encodestring(AUTH_STRING).decode().replace('\n', '')
HEADER = {"Authorization": ENC_AUTH_STRING,
          "Content-Type": "application/json", }
SEARCH_URL = JIRA_BASE_URL+'/rest/api/latest/search'
ISSUE_URL = JIRA_BASE_URL+'/rest/api/latest/issue/'
SEARCH_STR = 'project=JRA'
MAX_RESULTS = 1000 # max issues which could be processed in 1 iteration
JIRA_OUTPUT_FILE = 'D:/work/Jira_analyses/final_jira_out.json'
OUT_TEAM_TIME_REPORT = 'D:/work/Jira_analyses/team_time_report.csv'
TEAM = ['user1', 'user2']
jira_session = requests.session()
jira_session.headers = HEADER


try:
    jira_session.post(JIRA_BASE_URL)
except:
    print('Unable to connect or authenticate with JIRA server.')


def issues_by_jql(jql_string):
    """
    :param jql_string: string which represent JQL query used to find required Jira stories
    :return: extract from Jira of all queried stories in JSON  format
    """
    parameters = {'jql': jql_string,
                  'startAt': 0,
                  'maxResults': MAX_RESULTS,
                  # 'fields': 'key,status,assignee,creator,reporter,issuetype,project'}
                  'fields': '*all',
                  'expand': 'changelog'}
    result = jira_session.get(SEARCH_URL, params=parameters).json()
    total = result['total']
    if total > MAX_RESULTS:
        i = 1
        while MAX_RESULTS * i < total:
            parameters['startAt'] = MAX_RESULTS*i
            result['issues'] = result['issues']+jira_session.get(SEARCH_URL, params=parameters).json()['issues']
            i += 1
    print('Done extracting data from Jira')
    return result


def save_json_data(output_file, data):
    with open(output_file, 'w') as outfile:
        json.dump(data, outfile)


def get_list_from_file(file):
    """
    :param file: JSON file with data extracted from jira
    :return: list of JSON items (each item is jira story with full change history)
    """
    with open(file, 'r') as f:
        objects = ijson.items(f, 'issues.item')
        columns = list(objects)
    return columns


def row_list_to_df(list_to_parse):
    labels = ('KEY', 'ID', 'AUTHOR_NAME', 'AUTHOR_DISPLAY_NAME', 'ACTIVE', 'TIME_ZONE', 'FIELD',
              'OLD_VALUE', 'NEW_VALUE', 'OLD_NUM', 'NEW_NUM', 'DATE_CREATED')
    events = []
    for column in list_to_parse:
        for history in column['changelog']['histories']:
            date = parse(history['created'])
            date_str = str(date.day) + \
                        '.' + str(date.month) + \
                        '.' + str(date.year) + \
                        ' ' + str(date.hour) + \
                        ':' + str(date.minute) + \
                        ':' + str(date.second)
            for item in history['items']:
                try:
                    if (item['field'] == 'description') or item['field'] == 'Comment':
                        events.append((column['key']
                                      , history['id']
                                      , history['author']['name']
                                      , history['author']['displayName']
                                      , str(history['author']['active'])
                                      , history['author']['timeZone']
                                      , item['field']
                                      , 'skipped'
                                      , 'skipped'
                                      , 'skipped'
                                      , 'skipped'
                                      , date_str))
                    else:
                        events.append((column['key']
                                      , history['id']
                                      , history['author']['name']
                                      , history['author']['displayName']
                                      , str(history['author']['active'])
                                      , history['author']['timeZone']
                                      , item['field']
                                      , str(item['fromString'])
                                      , str(item['toString'])
                                      , str(item['from'])
                                      , str(item['to'])
                                       , date_str))
                except TypeError:
                    print(history['id'])
                    continue
    out_df = pd.DataFrame.from_records(events, columns=labels)
    return out_df


def df_transform(src_df):
    """
    Adding end_dates column to source data frame. end dates are nothing but start_dates shifted on 1 value
    since each new line has start date which is end date for previous status
    """
    end_dates = src_df['DATE_CREATED'].tolist()
    end_dates.pop(0)
    end_dates.append('null')
    src_df = src_df.assign(END_DATES=pd.Series(end_dates))
    """
    Set last end_date for each story as a last update date of the story
    """
    old_value = src_df.iloc[0]
    for index, row in src_df.iterrows():
        if old_value.KEY != row.KEY:
            src_df.loc[src_df.index[index - 1], 'END_DATES'] = \
                src_df.loc[src_df.index[index - 1], 'DATE_CREATED']
        old_value = row
        src_df.loc[src_df.index[len(src_df) - 1], 'END_DATES'] = \
            src_df.loc[src_df.index[len(src_df) - 1], 'DATE_CREATED']
    """
    Add time difference in hours
    """
    time = src_df[['DATE_CREATED', 'END_DATES']].apply(lambda x: dt.strptime(x['END_DATES'], '%d.%m.%Y %H:%M:%S')
                                                                - dt.strptime(x['DATE_CREATED'],
                                                                                    '%d.%m.%Y %H:%M:%S'), axis=1)
    time_h = [round(a.total_seconds() / 3600) for a in time]
    src_df = src_df.assign(DURATION=pd.Series(time_h))
    # users.to_csv(SAVE_FILE, index=None, sep=';', mode='a')
    return src_df


def calc_story_teams_time(in_df, in_team):
    """
    :param in_df: input DataFrame which need to be processed
    :param names: list of team members which need to be processed
    :return: will return resulting DataFrame
    """
    start_range = 0
    stop_range = 0
    new_team = ''
    if 'assignee' not in in_df['FIELD'].unique():
        in_df['OLD_NUM'].values[0:] = 'NOT_DEFINED'
        return in_df
    for i in range(len(in_df)):
        if in_df['FIELD'].values[i] != 'assignee':
            if i == len(in_df) - 1:
                if len(new_team) == 0:
                    in_df['OLD_NUM'].values[start_range:stop_range + 1] = in_df['OLD_NUM'].values[
                        max(start_range - 1, 0)]
                else:
                    in_df['OLD_NUM'].values[start_range:stop_range + 1] = new_team
            stop_range += 1
        elif in_df['FIELD'].values[i] == 'assignee':
            if in_df['OLD_NUM'].values[i] in in_team:
                in_df['OLD_NUM'].values[start_range:stop_range + 1] = 'OUR_TEAM'
            elif in_df['OLD_NUM'].values[i] == 'None':
                in_df['OLD_NUM'].values[start_range:stop_range + 1] = 'NOT_ASSIGNED'
            else:
                in_df['OLD_NUM'].values[start_range:stop_range + 1] = 'NOT_OUR_TEAM'
            if in_df['NEW_NUM'].values[i] in in_team:
                new_team = 'OUR_TEAM'
            elif in_df['NEW_NUM'].values[i] == 'None':
                new_team = 'NOT_ASSIGNED'
            else:
                new_team = 'NOT_OUR_TEAM'
            stop_range += 1
            start_range = stop_range
    return in_df


def get_teams_time(in_df):
    keys = in_df['KEY'].unique()
    result_list = []
    for key in keys:
        new_df = df_to_use[df_to_use['KEY'] == key].reset_index()
        result_list.append(calc_story_teams_time(new_df, TEAM))
    return pd.concat(result_list, ignore_index=True).groupby(['KEY', 'OLD_NUM'])[['DURATION']].sum()


# get json data by JQL string
issues = issues_by_jql(SEARCH_STR)
# save source data to file
save_json_data(JIRA_OUTPUT_FILE, issues)
# get list of jira stories from source file
source_list = get_list_from_file(JIRA_OUTPUT_FILE)
# transform stories to pandas DataFrame
df_to_use = df_transform(row_list_to_df(source_list))
# calculate time spent on stories
teams_df = get_teams_time(df_to_use)
# save report to CSV file
teams_df.to_csv(OUT_TEAM_TIME_REPORT, encoding="utf-8-sig", sep=';', mode='a')

