from flask import Flask, render_template
from flask import request
import json
import plotly
from flask_cors import CORS
import datetime

from data_processing import preprocessing, system_fault, fault_database

app = Flask(__name__)
CORS(app)


@app.route('/get_sql_ids')
def get_sql_id_list():
    path = "resources/sql_ids.txt"
    sql_id_list = []
    file_sql_id = open(path)

    for line in file_sql_id:
        sql_id_list.append(line)

    graph_json = json.dumps(sql_id_list)
    return graph_json


@app.route('/plot', methods=['GET'])
def plot_sys_fault():
    print("start_time: " + str(datetime.datetime.now()))
    sql_id = request.args.get('sql_id', None)
    days_num = request.args.get('days_num', None)

    # get the data dictionary
    path_log = "C:/Users/DM3522/Desktop/access.log"
    path_fault = "resources/faults.txt"

    # check if we have enough data
    sql_stores_dict = preprocessing.get_preprocessed_data(days=int(days_num), path_file=path_log)
    if len(sql_stores_dict) == 0 or int(sql_id) not in sql_stores_dict.keys():
        return 'Data is not available in the specified days. Please increase the days number', 400

    fig = creat_fig(sql_stores_dict, int(sql_id), path_fault)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print("End_time: " + str(datetime.datetime.now()))
    return graph_json


@app.route('/')
def home():
    return render_template('sys-fault.html')


def creat_fig(sql_stores_dict, sql_id, path_fault):
    # configuration
    time_interval = 10
    acceptance_rate = 0.9
    min_valid_pair_intervals = 20
    window_size = 500
    sql_id_plot = sql_stores_dict.copy()

    # if the current configuration is match with the data in file, we check the last_update and try to find the faults
    # after that time
    is_database_valid = fault_database.is_valid_database(time_interval, acceptance_rate, min_valid_pair_intervals,
                                                         path_fault)
    if is_database_valid:
        last_database_update = fault_database.get_last_update(path_fault)
        sql_stores_dict = preprocessing.limit_sql_id(sql_stores_dict, last_database_update)

    if is_database_valid:
        if len(sql_stores_dict) != 0:
            grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=time_interval)
            # detect the fault time intervals in the system
            sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=acceptance_rate,
                                                     min_valid_pair_intervals=min_valid_pair_intervals)
            # reading all faults from file
            sys_fault = fault_database.get_saved_faults(path_fault) + sys_fault
        else:
            # grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=time_interval)
            # # detect the fault time intervals in the system
            # sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=acceptance_rate,
            #                                          min_valid_pair_intervals=min_valid_pair_intervals)
            sys_fault = fault_database.get_saved_faults(path_fault)
    else:
        grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=time_interval)
        # detect the fault time intervals in the system
        sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=acceptance_rate,
                                                 min_valid_pair_intervals=min_valid_pair_intervals)

    # show the graph on moving average
    moved_average = preprocessing.moving_average(sql_id_plot[sql_id], window_size=window_size)
    return system_fault.plot_sys_fault(moved_average, sql_id, sys_fault, time_interval=time_interval)
