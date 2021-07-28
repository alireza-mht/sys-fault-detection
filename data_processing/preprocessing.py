import numpy as np
import datetime
import logging
import pandas as pd
import os


def read_date(path_dir, days=None):
    if days is not None:
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(days=days)
    else:
        start_time = datetime.datetime.min
    current_dir = os.getcwd()
    # Change the directory
    os.chdir(path_dir)
    if len(os.listdir()) == 0:
        logging.warning("There is not any log file to be processed")

    code_status = '200'
    data = []
    # iterate through all file
    for log_file in reversed(os.listdir()):
        # Check whether file is in text format or not
        if log_file.endswith(".txt"):
            file_path = path_dir + os.sep + log_file
            file = open(file_path)
            lines = file.read().splitlines()

            # we start iterating from end to be able to break the for loop. Better performance
            for line in reversed(lines):
                # some data do not have sql_id
                if "sqlstore_id" in line:
                    data_line = line.split()
                    if data_line[1] != '-':
                        date_index = 1
                    else:
                        date_index = 3

                    line_date = data_line[date_index].replace('[', '').replace(':', ' ', 1)
                    line_date = datetime.datetime.strptime(line_date, '%d/%b/%Y %H:%M:%S')
                    # break if the line_date exceeded the request date
                    if line_date < start_time:
                        file.close()
                        os.chdir(current_dir)
                        # return from latest time up until now
                        return reversed(data)

                    if len(data_line) == 10:
                        status_index = 8
                        sql_id_index = 6
                        time_index = 9
                    else:
                        status_index = 7
                        sql_id_index = 5
                        time_index = 8

                    if data_line[status_index] == code_status:
                        sql_id = data_line[sql_id_index].split("sqlstore_id=")[1].split("&")[0]
                        # some data do not have response time and some of them have error
                        if data_line[time_index].isdigit() and sql_id != 'null':
                            data.append(
                                [line_date,
                                 np.int64(data_line[sql_id_index].split("sqlstore_id=")[1].split("&")[0]),
                                 np.int64(data_line[time_index])])

            file.close()
        else:
            logging.warning("Log file is not in .txt format")

    os.chdir(current_dir)
    # return from latest time up until now
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
        response_time = np.array([ele[2] for ele in sql_data[dict]])
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
    """ reading all the sql_id from the log file and group all the data based on the sql_id

                Parameters:
                    path_file: path to the access.log
                    days: just read and process the data from just specific days ago

                return :
                    dictionary of all the sql_ids in the last n days. The key of dictionary is the sql_ids and the
                    value of dictionary includes two list. The first one is the date and the second list is the latency.
                    values in these lists are mapped to each other
    """

    logging.debug("preprocessing data started")
    data = read_date(path_file, days)
    sql_store_dict = grouped_by_sql_store_id(data)
    return sql_store_dict


def get_info_for_sql_id(path_file, days, sql_id):
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(days=days)
    start_time = datetime.datetime(year=start_time.year, month=start_time.month, day=1)
    # try:
    file = open(path_file)

    lines = file.read().splitlines()
    data = []
    date = []
    ip_address = []
    for line in reversed(lines):
        data_line = line.split()
        line_date = data_line[3].replace('[', '').replace(':', ' ', 1)
        line_date = datetime.datetime.strptime(line_date, '%d/%b/%Y %H:%M:%S')

        # break if the line_date exceeded the request date
        if line_date < start_time:
            break

        # some data do not have sql_id
        if "sqlstore_id" in line:
            sql_id_log = data_line[6].split("sqlstore_id=")[1].split("&")[0]

            # some data do not have response time and some of them have error
            if data_line[9].isdigit() and sql_id_log != 'null' and sql_id_log == sql_id:
                date.append(line_date)
                ip_address.append(data_line[0])
                # data.append(
                #     [line_date,
                #      np.int64(data_line[6].split("sqlstore_id=")[1].split("&")[0]),
                #      data_line[0]])
    dictionary = {
        "date": date,
        "sql_id": sql_id,
        "ip_address": ip_address
    }
    return dictionary


def limit_sql_id(sql_ids, time):
    """ remove the data before a special date for all the sql_ids

            Parameters:
                sql_ids: all the sql_ids in a dictionary
                time: remove the sql_ids before this time in string

            return :
                dictionary of all the sql_ids after the mentioned time
    """

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


def get_number_of_requests_per_month(dates):
    # dates.append(time_now)
    sample_x_pd = pd.to_datetime(dates)
    df = pd.DataFrame(sample_x_pd, columns=['Date'])
    df['Count'] = np.ones(len(dates))
    freq_rate = '1MS'
    grouped = df.groupby(pd.Grouper(key='Date', freq=freq_rate)).sum()
    grouped_reset = grouped.reset_index()
    Row_list = []

    # Iterate over each row
    for index, rows in grouped_reset.iterrows():
        # Create list for the current row
        my_list = [rows.Date, rows.Count]

        # append the list to the final list
        Row_list.append(my_list)
    return Row_list


# [grouped.index.values.astype('M8[s]').astype('O'), grouped['Count'].values]


def get_number_of_ip(dates, ip_addresses):
    time_now = datetime.datetime.now()
    # dates.append(time_now)
    # ip_addresses.append(" ")

    sample_x_pd = pd.to_datetime(dates)

    df = pd.DataFrame(sample_x_pd, columns=['Date'])
    df.insert(1, 'Ip', ip_addresses)

    df['Count'] = np.concatenate((np.ones(len(dates) - 1), np.zeros(1)), axis=0)
    freq_rate = '1MS'
    grouped_by_date_ip = df.groupby([pd.Grouper(key='Date', freq=freq_rate), "Ip"]).sum()
    df = grouped_by_date_ip.reset_index()
    # df_date_ip = pd.DataFrame(grouped_by_date_ip)
    # grouped_by_date = reset.groupby(['Date'])
    # print(grouped_by_date.head())
    Row_list = []

    # Iterate over each row
    for index, rows in df.iterrows():
        # Create list for the current row
        my_list = [rows.Date, rows.Ip, rows.Count]

        # append the list to the final list
        Row_list.append(my_list)

    return Row_list