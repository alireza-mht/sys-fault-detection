from flask import Flask, render_template, Response
from flask import request
import json
import plotly
from flask_cors import CORS
from getopt import getopt, GetoptError
from logging.handlers import RotatingFileHandler
from flask.logging import default_handler
import os
import sys
import logging
from data_processing import preprocessing, system_fault, fault_database

app = Flask(__name__)
CORS(app)

# --------------------------------
#        Configuration
# --------------------------------

config_file = None
try:
    opts, args = getopt(sys.argv[1:], "c:", ["config="])
    for opt, arg in opts:
        if opt in '-c, --config':
            config_file = arg
except GetoptError:
    pass
if not config_file:
    config_file = os.path.abspath(
        os.path.dirname(__file__) + os.sep + 'config' + os.sep + 'config.json')
    print('Assuming config file at: ' + config_file)
if not os.path.exists(config_file):
    print('config file: ' + config_file + ' not found')
    exit(-1)
app.config.from_json(config_file)

# --------------------------------
#       Logger Settings
# --------------------------------

root = logging.getLogger()
root.addHandler(default_handler)

os.makedirs(app.config['LOG_DIR'], exist_ok=True)
rotating_handler = RotatingFileHandler(app.config['LOG_DIR'] + os.sep + 'fault_detection.log',
                                       maxBytes=app.config['LOG_MAX_SIZE'],
                                       backupCount=app.config['LOG_MAX_FILES'])
formatter = logging.Formatter('[%(asctime)s] %(levelname)s : %(message)s')
rotating_handler.setFormatter(formatter)
root.addHandler(rotating_handler)

if app.config['DEBUG']:
    root.setLevel(logging.DEBUG)
else:
    root.setLevel(logging.INFO)

root.info('Service faults_detection started')
root.info('Service faults_detection configuration file: ' + config_file)
root.info('Service faults_detection logs of reports: ' + app.config['LOG_DIR'])


# --------------------------------
#           routes
# --------------------------------

@app.route('/get_sql_ids')
def get_sql_id_list():
    path = app.config['SQL_ID_DATA_DIR']
    sql_id_list = []
    try:
        file_sql_id = open(path)
    except FileNotFoundError as e:
        root.error(e, exc_info=True)
        return Response("file not found", status=500, mimetype='text/xml')

    for line in file_sql_id:
        sql_id_list.append(line)

    graph_json = json.dumps(sql_id_list)
    return Response(graph_json, status=200, mimetype='application/json')


@app.route('/plot', methods=['GET'])
def plot_sys_fault():
    sql_id = request.args.get('sql_id', None)
    days_num = request.args.get('days_num', None)
    path_log = app.config['LOG_DATA_DIR']
    path_fault = app.config['FAULT_DATA_DIR']

    # check if we have enough data
    try:
        sql_stores_dict = preprocessing.get_preprocessed_data(days=int(days_num), path_file=path_log)
    except FileNotFoundError as e:
        root.error(e, exc_info=True)
        return Response("file not found", status=500, mimetype='text/xml')


    if len(sql_stores_dict) == 0 or int(sql_id) not in sql_stores_dict.keys():
        logging.warning("Request not completed due to unavailability of data")
        return Response("Data is not available in the specified days. Please increase the days number", status=400,
                        mimetype='text/xml')

    fig = creat_fig(sql_stores_dict, int(sql_id), path_fault)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    root.info("plotting is finished")
    return Response(graph_json, status=200, mimetype='application/json')


@app.route('/')
def home():
    return render_template('sys-fault.html')


def creat_fig(sql_stores_dict, sql_id, path_fault):
    # configuration
    time_interval = app.config['TIME_INTERVAL']
    acceptance_rate = app.config['ACCEPTANCE_RATE']
    min_valid_pair_intervals = app.config['MIN_VALID_PAIR_INTERVAL']
    window_size = app.config['WINDOWS_SIZE_MOVING_AVERAGE']
    sql_id_plot = sql_stores_dict.copy()

    is_database_valid = False
    try:
        is_database_valid = fault_database.is_valid_database(time_interval, acceptance_rate, min_valid_pair_intervals,
                                                             path_fault)
    except OSError as e:
        root.error(e, exc_info=True)

    # if the current configuration is matched with the data in fault.txt, we check the last_update and try to find the
    # faults after the last updated time
    if is_database_valid:
        root.info("Faults text file is valid. Start reading the faults from text file.")
        last_database_update = fault_database.get_last_update(path_fault)
        sql_stores_dict = preprocessing.limit_sql_id(sql_stores_dict, last_database_update)

        # if we have new data after the last updated time in database
        if len(sql_stores_dict) != 0:
            root.info("Database is not updated. Start finding faults among new added data")
            grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=time_interval)
            # detect the fault time intervals in the system
            sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=acceptance_rate,
                                                     min_valid_pair_intervals=min_valid_pair_intervals)
            # reading all faults from file
            sys_fault = fault_database.get_saved_faults(path_fault) + sys_fault
        else:
            sys_fault = fault_database.get_saved_faults(path_fault)
    else:
        root.warning("Database configuration is not valid")
        root.info("Start processing all the data.")
        grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=time_interval)
        # detect the fault time intervals in the system
        sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=acceptance_rate,
                                                 min_valid_pair_intervals=min_valid_pair_intervals)

    # show the graph on moving average
    moved_average = preprocessing.moving_average(sql_id_plot[sql_id], window_size=window_size)
    return system_fault.plot_sys_fault(moved_average, sql_id, sys_fault, time_interval=time_interval)


@app.errorhandler(Exception)
def handle_exception(e):
    root.error(e, exc_info=True)
    return Response("Check the logs for more information on the error", status=500, mimetype='text/xml')
