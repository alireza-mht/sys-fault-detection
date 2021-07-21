import numpy as np
import datetime
import logging


def read_date(path_file, days=None):
    if days is not None:
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(days=days)
    else:
        start_time = datetime.datetime.min

    # try:
    file = open(path_file)
    # except OSError as e:
    #     logging.error(e, exc_info=True)
    #     raise

    lines = file.read().splitlines()
    data = []

    # we start iterating from end to be able to break the for loop. Better performance
    for line in reversed(lines):
        data_line = line.split()
        line_date = data_line[3].replace('[', '').replace(':', ' ', 1)
        line_date = datetime.datetime.strptime(line_date, '%d/%b/%Y %H:%M:%S')

        # break if the line_date exceeded the request date
        if line_date < start_time:
            break

        # some data do not have sql_id
        if "sqlstore_id" in line:
            sql_id = data_line[6].split("sqlstore_id=")[1].split("&")[0]

            # some data do not have response time and some of them have error
            if len(data_line) == 10 and data_line[9].isdigit() and sql_id != 'null':
                data.append(
                    [line_date,
                     np.int64(data_line[6].split("sqlstore_id=")[1].split("&")[0]),
                     np.int64(data_line[8]), np.int64(data_line[9])])

    return reversed(data)


def grouped_by_sql_store_id(data):
    sql_data = {}
    for line in data:
        if line[1] not in sql_data.keys():
            sql_data[line[1]] = list()
            sql_data[line[1]].append(line)
        else:
            sql_data[line[1]].append(line)

    sql_processed = {}
    for dict in sql_data:
        sql_processed[dict] = list()
        response_time = np.array([ele[3] for ele in sql_data[dict]])
        date = np.array([ele[0] for ele in sql_data[dict]])
        sql_processed[dict].append(date)
        sql_processed[dict].append(response_time)

    return sql_processed


def moving_average(data, window_size):
    data_y = data[1]
    if len(data_y) < window_size:
        window_size = len(data_y)

    moving_averages = []
    for i in range(len(data_y) - window_size + 1):
        this_window = data_y[i: i + window_size]

        window_average = sum(this_window) / window_size
        moving_averages.append(window_average)

    for i in range(len(data_y) - window_size + 1, len(data_y)):
        this_window = data_y[i:]
        window_average = sum(this_window) / len(this_window)
        moving_averages.append(window_average)

    return [data[0], moving_averages]


def get_preprocessed_data(path_file, days=None):
    logging.debug("preprocessing data started")
    data = read_date(path_file, days)
    sql_store_dict = grouped_by_sql_store_id(data)
    return sql_store_dict


def limit_sql_id(sql_ids, time):
    logging.debug("sql id limitation started")
    time = datetime.datetime.strptime(time, '%Y/%m/%d-%H:%M:%S')
    empty_sql_id = []
    for sql_id in sql_ids:
        date = sql_ids[sql_id][0]
        response_time = sql_ids[sql_id][1]
        data_final = []
        response_time_final = []
        for i in range(len(date) - 1, -1, -1):
            if date[i] > time:
                data_final.insert(0, date[i])
                response_time_final.insert(0, response_time[i])

            else:
                break

        if len(data_final) != 0:
            sql_ids[sql_id][0] = np.array(data_final)
            sql_ids[sql_id][1] = np.array(response_time_final)
        else:
            empty_sql_id.append(sql_id)

    [sql_ids.pop(v) for v in empty_sql_id]
    return sql_ids





