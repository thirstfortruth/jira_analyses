import pandas as pd
import ijson
from dateutil.parser import parse


FILENAME = 'E:\work\my tasks\Jira_analyses\json_out_bckp.json'
OUT_FILENAME = 'E:\work\my tasks\Jira_analyses\out_csv.csv'


def get_list_from_file(file):
    with open(file, 'r') as f:
        objects = ijson.items(f, 'issues.item')
        columns = list(objects)
    return columns
    # print(len(columns))
    # print(columns[0])


def parse_file(out_filename, list_to_parse):
    with open(out_filename, 'w') as file:
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


get_list = get_list_from_file(FILENAME)
parse_file(OUT_FILENAME, get_list)


