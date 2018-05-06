import pandas as pd
import ijson
from datetime import datetime as dt
from dateutil.parser import parse


# FILENAME = 'E:\work\my tasks\Jira_analyses\json_out_bckp.json'
# OUT_FILENAME = 'E:\work\my tasks\Jira_analyses\out_csv1.csv'
FILENAME = 'D:\work\Jira_analyses\json_out_bckp.json'
OUT_FILENAME = 'D:\work\Jira_analyses\out_csv.csv'
OUT_NEW_FILENAME = 'D:\work\Jira_analyses\out_new_csv.csv'
OUT_TEAM_FILENAME = 'D:\work\Jira_analyses\out_team_time.csv'
TEAM = ['ic16', 'ead7', 'uke12358537', 'ead6', 'fc82', 'ib19']

def get_list_from_file(file):
    with open(file, 'r') as f:
        objects = ijson.items(f, 'issues.item')
        columns = list(objects)
    return columns


def parse_file_simple(out_filename, list_to_parse):
    with open(out_filename, 'w', encoding='utf-8') as file:
        file.write('KEY;AUTHOR_NAME;DATE_CREATED;OLD_VALUE;NEW_VALUE;OLD_NUM;NEW_NUM\n')
        for column in list_to_parse:
            for history in column['changelog']['histories']:
                for item in history['items']:
                    if item['field'] == 'status':
                        date = parse(history['created'])
                        date_str = str(date.day) + \
                                   '.' + str(date.month) + \
                                   '.' + str(date.year) + \
                                   ' ' + str(date.hour) + \
                                   ':' + str(date.minute) + \
                                   ':' + str(date.second)
                        file.write(column['key'] +
                                   ';' + history['author']['name'] +
                                   ';' + date_str +
                                   ';' + item['fromString'] +
                                   ';' + item['toString'] +
                                   ';' + item['from'] +
                                   ';' + item['to'] +
                                   '\n')


def list_to_csv(out_filename, list_to_parse):
    with open(out_filename, 'w', encoding='utf-8') as file:
        file.write('KEY;ID;AUTHOR_NAME;AUTHOR_DISPLAY_NAME;ACTIVE;TIME_ZONE;DATE_CREATED;FIELD;OLD_VALUE;NEW_VALUE;'
                   'OLD_NUM;NEW_NUM\n')
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
                            file.write(column['key'] +
                                       ';' + history['id'] +
                                       ';' + history['author']['name'] +
                                       ';' + history['author']['displayName'] +
                                       ';' + str(history['author']['active']) +
                                       ';' + history['author']['timeZone'] +
                                       ';' + date_str +
                                       ';' + item['field'] +
                                       ';' + 'skipped' +
                                       ';' + 'skipped' +
                                       ';' + 'skipped' +
                                       ';' + 'skipped' +
                                       '\n')
                        else:
                            file.write(column['key'] +
                                       ';' + history['id'] +
                                       ';' + history['author']['name'] +
                                       ';' + history['author']['displayName'] +
                                       ';' + str(history['author']['active']) +
                                       ';' + history['author']['timeZone'] +
                                       ';' + date_str +
                                       ';' + item['field'] +
                                       ';' + str(item['fromString']) +
                                       ';' + str(item['toString']) +
                                       ';' + str(item['from']) +
                                       ';' + str(item['to']) +
                                       '\n')
                    except TypeError:
                        print(history['id'])
                        continue


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


def change_type_sum(in_df, change_field):
    """
    :param in_df: input dataframe which need to be processed
    :param change_field: field by which we need to make calculation
    :return: resulting DataFrame
    This function used to summarize time spent on some specific types of changes.
    For example if type will be "status", function will return for each story sum of time in different status
    """
    for index, row in in_df.iterrows():
        print(index, row)
    return 0


def normalize_group(df_in):
    """
    :param df_in: input DataFrame which need to be processed
    :return: will return resulting DataFrame
    """
    inital_raw = df_in.iloc[0]
    # df_in.loc[df_in['FIELD'] != 'status', 'FIELD'] = 'status'
    return df_in

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


source_list = get_list_from_file(FILENAME)
df_to_use = df_transform(row_list_to_df(source_list))
teams_df = get_teams_time(df_to_use)
teams_df.to_csv(OUT_TEAM_FILENAME, encoding="utf-8-sig", sep=';', mode='a')
# df_to_use.to_csv(OUT_NEW_FILENAME, index=None, encoding="utf-8-sig", sep=';', mode='a')

    # print(new_df.values[i])
# print(full_dataframe.groupby(['FIELD']))

# list_to_csv(OUT_FILENAME, source_list)
