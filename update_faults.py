import datetime
from data_processing import preprocessing, system_fault, fault_database
from getopt import getopt, GetoptError
import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler


def update_faults(path_log, path_fault, interval, rate, min_valid_pair):
    root.debug("start updating")

    is_database_valid = False
    try:
        is_database_valid = fault_database.is_valid_database(time_interval, acceptance_rate, min_valid_pair_intervals,
                                                             path_fault)
    except OSError as e:
        root.error(e, exc_info=True)
        print("There is not such file or directory!")
        exit(-1)

    time_now = datetime.datetime.now()
    if is_database_valid:
        root.info("database is valid. start finding the faults in the new added data!")
        last_update = fault_database.get_last_update(path_fault)
        last_update_datetime = datetime.datetime.strptime(last_update, '%Y/%m/%d-%H:%M:%S')
        time_delta = time_now - last_update_datetime
        time_delta = time_delta.days
        sql_stores_dict = preprocessing.get_preprocessed_data(days=time_delta + 1, path_file=path_log)
    else:
        root.warning("fault.txt is not valid. start calculating the faults with new configuration!")
        fault_database.creat_database(time_interval, rate, min_valid_pair, time_now, path_fault)
        sql_stores_dict = preprocessing.get_preprocessed_data(path_file=path_log)

    if len(sql_stores_dict) != 0:
        grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=interval)
        sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=rate,
                                                 min_valid_pair_intervals=min_valid_pair)
        fault_database.write_new_faults(time_now, sys_fault, path=path_fault)
    else:
        root.warning("there is not any new data")
    root.debug("faults.txt is updated")


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
with open(os.path.dirname(__file__) + os.sep + 'config' + os.sep + 'config.json', 'r') as f:
    config = json.load(f)

# --------------------------------
#       Logger Settings
# --------------------------------

root = logging.getLogger()
os.makedirs(config['LOG_DIR'], exist_ok=True)
rotating_handler = RotatingFileHandler(config['LOG_DIR'] + os.sep + 'update_faults.log',
                                       maxBytes=config['LOG_MAX_SIZE'],
                                       backupCount=config['LOG_MAX_FILES'])
formatter = logging.Formatter('[%(asctime)s] %(levelname)s : %(message)s')
rotating_handler.setFormatter(formatter)
root.addHandler(rotating_handler)

if config['DEBUG']:
    root.setLevel(logging.DEBUG)
else:
    root.setLevel(logging.INFO)

root.info('Service update_faults started')
root.info('Service update_faults configuration file: ' + config_file)
root.info('Service update_faults logs of reports: ' + config['LOG_DIR'])

# --------------------------------
#       Load configuration
# --------------------------------

path_log = config['LOG_DATA_DIR']
path_fault = config['FAULT_DATA_DIR']
time_interval = config['TIME_INTERVAL']
acceptance_rate = config['ACCEPTANCE_RATE']
min_valid_pair_intervals = config['MIN_VALID_PAIR_INTERVAL']

# --------------------------------
#               Run
# --------------------------------

days_interval = 2
time_to_run = "03:00"
root.info('start updating faults.txt every ' + str(days_interval) + ' days at time ' + time_to_run)
update_faults(path_log, path_fault, time_interval, acceptance_rate, min_valid_pair_intervals)
