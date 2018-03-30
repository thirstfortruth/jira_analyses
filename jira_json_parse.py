import pandas as pd
import ijson
from dateutil.parser import parse


FILENAME = 'E:\work\my tasks\Jira_analyses\json_out_bckp.json'
#OUT_FILENAME = 'D:\work\Jira_analyses\out_csv.csv'
OUT_FILENAME = 'E:\work\my tasks\Jira_analyses\out_csv1.csv'


def get_list_from_file(file):
    with open(file, 'r') as f:
        objects = ijson.items(f, 'issues.item')
        columns = list(objects)
    return columns
    # print(len(columns))
    # print(columns[0])


def check_empty(in_object):
    if not in_object:
        return 'None'


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
                        # print(parse(history['created']))


def parse_file_detailed(out_filename, list_to_parse):
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
#                'id': '4166400',
#                'author': {
#                    'self': 'https: //jira.global.tesco.org/rest/api/2/user?username=pr10',
#                     'name': 'pr10',
#                     'key': 'pr10',
#                     'emailAddress': 'damien.mcgarrigle@tesco.com',
#                     'displayName': 'McGarrigle,
#                     Damien',
#                           'active': True,
#                                     'timeZone': 'Europe/London'
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
    print('')

get_list = get_list_from_file(FILENAME)
#print(get_list[0])
#parse_file_simple(OUT_FILENAME, get_list)
#test = None
#print('1'+check_empty(test)+'2')
parse_file_detailed(OUT_FILENAME, get_list)
