import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as go


def roundTime(dt=None, roundTo=60):
    """Round a datetime object to any time lapse in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if dt == None: dt = datetime.datetime.now()
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + roundTo / 2) // roundTo * roundTo
    return dt - datetime.timedelta(0, rounding - seconds, -dt.microsecond)


#
def group_average_by_minutes(samples, minutes, start_time, end_time):
    """ group the moving average of one specific sql_id based on the defined start time and end time

        return:
            grouped data by the defined min, average latency in each time interval
    """

    sample_x = samples[0]
    sample_y = samples[1]

    based_diff_start = (sample_x[0] - start_time).total_seconds()
    based_diff_end = (end_time - sample_x[-1]).total_seconds()

    # reform the data size to be started from start time
    if based_diff_start > (minutes * 60):
        sample_x = np.insert(sample_x, 0,
                             start_time, axis=0)
        sample_y = np.insert(sample_y, 0, 0, axis=0)

    # reform the data size to be ended in end time
    if based_diff_end > (minutes * 60):
        sample_x = np.append(sample_x, end_time)
        sample_y = np.append(sample_y, 0)

    # we want to use groupby method of panda
    sample_x_pd = pd.to_datetime(sample_x)
    df = pd.DataFrame(sample_x_pd, columns=['Date'])
    df['latency'] = sample_y

    # define the freq_rate for grouping the data (in sec)
    freq_rate = str(minutes * 60) + 'S'
    grouped_data = df.groupby(pd.Grouper(key='Date', freq=freq_rate)).mean().fillna(0)

    return [grouped_data.index.values, grouped_data['latency'].values]


#
def calculate_fault(grouped_by_minutes, acceptance_rate, min_valid_pair_intervals):
    """ Find the faults intervals in the system

        Parameters:
            acceptance_rate: a rate for detecting the faults
            min_valid_pair_intervals: minimum number of required valid interval to detect the faults in the system

        return :
            list of start time and end time of system faults
    """

    # get the first value to check the size of sql_ids
    values = grouped_by_minutes.values()
    value_iterator = iter(values)
    first_value = next(value_iterator)

    interval_size = len(first_value[0])

    fault_pair_time_intervals = []

    for i in range(interval_size - 1):
        number_of_increase = 0

        # valid interval: the interval which does not have zero value
        number_of_valid_pair_interval = 0

        for dic in grouped_by_minutes:
            # if we have a sql request on the interval we will count it
            if grouped_by_minutes[dic][1][i] != 0 and grouped_by_minutes[dic][1][i + 1] != 0:
                number_of_valid_pair_interval += 1

            # if we have an increase we will count it
            if (grouped_by_minutes[dic][1][i + 1] > grouped_by_minutes[dic][1][i] != 0 and
                    grouped_by_minutes[dic][1][i + 1] != 0):
                number_of_increase += 1

        # check if there is system fault
        if number_of_valid_pair_interval > min_valid_pair_intervals:
            if number_of_increase > (acceptance_rate * number_of_valid_pair_interval):
                first_time_interval = first_value[0][i]
                second_time_interval_plus_one = first_value[0][i + 1]
                fault_pair_time_intervals.append((first_time_interval, second_time_interval_plus_one))

    return fault_pair_time_intervals


def group_by_minutes(sql_store_dict, time_interval):
    """ group all the sql_ids based on the minimum start time and maximum end time of all sql_ids

    """
    grouped_by_minutes = {}

    # find the minimum time and maximum time of all sql_ids in all sql_id data starts from start time and ends by the
    # end time all sql id will have the same size based on the time interval
    start_time = min([v[0][0] for v in sql_store_dict.values()])
    end_time = max([v[0][-1] for v in sql_store_dict.values()])

    # rounding the start time and end time to the closest time interval
    start_time_round = start_time - datetime.timedelta(minutes=start_time.minute % time_interval,
                                                       seconds=start_time.second,
                                                       microseconds=start_time.microsecond)
    end_time_round = end_time - datetime.timedelta(minutes=end_time.minute % time_interval,
                                                   seconds=end_time.second,
                                                   microseconds=end_time.microsecond)

    # group all the data in all sql_ids based on the time_interval
    for dic in sql_store_dict:
        grouped_by_minutes[dic] = group_average_by_minutes(sql_store_dict[dic], time_interval, start_time_round,
                                                           end_time_round
                                                           )
    return grouped_by_minutes


def plot_sys_fault(sample, sql_id, sys_fault=None):
    sample_x = sample[0]
    sample_y = sample[1]

    first_fault_interval_x = []
    first_fault_interval_y = []

    second_fault_interval_x = []
    second_fault_interval_y = []

    for i in range(len(sample_x)):
        for j in range(len(sys_fault)):

            # mark the sys fault data in the first interval
            if sys_fault[j][0] < np.datetime64(sample_x[i]) < sys_fault[j][1]:
                first_fault_interval_x.append(sample_x[i])
                first_fault_interval_y.append(sample_y[i])

            # mark the sys fault data in the second interval
            elif (sys_fault[j][0] + np.timedelta64(10, 'm')) < np.datetime64(sample_x[i]):
                if np.datetime64(sample_x[i]) < (sys_fault[j][1] + np.timedelta64(10, 'm')):
                    second_fault_interval_x.append(sample_x[i])
                    second_fault_interval_y.append(sample_y[i])

    # create figures
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=first_fault_interval_x, y=first_fault_interval_y, mode='markers', marker=dict(
            color='blue'), name='requests in a first fault '
                                'interval'))

    fig.add_trace(
        go.Scatter(x=second_fault_interval_x, y=second_fault_interval_y, mode='markers', marker=dict(
            color='black'),
                   name='requests in a second fault interval'))
    fig.add_trace(go.Scatter(x=sample_x, y=sample_y, mode='lines', marker=dict(
        color='red'), name='moved_average'))
    fig.update_layout(title="Moving averages and system faults for id=" + str(sql_id),
                      xaxis_title="Date and time",
                      yaxis_title="Response time"
                      )

    fig.update_layout(showlegend=True)
    return fig
