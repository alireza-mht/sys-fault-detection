import time
import schedule
from getopt import getopt, GetoptError
import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler


def save_sql_id_list(path_file, path_sqls):
    root.debug("start updating the sql_ids.txt")
    file_log = open(path_file)
    lines = file_log.read().splitlines()
    data = []

    try:
        file = open(path_sqls, "w")
    except Exception as e:
        root.error(e, exc_info=True)
        print("There is no file or such directory!")
        exit(-1)

    with file as file_save:
        # we start iterating from end to be able to break the for loop. Better performance
        for line in reversed(lines):
            data_line = line.split()

            # some data do not have sql_id
            if "sqlstore_id" in line:
                sql_id = data_line[6].split("sqlstore_id=")[1].split("&")[0]
                if sql_id != "null" and int(sql_id) not in data:
                    data.append(int(sql_id))
                    file_save.write(sql_id + "\n")
    root.debug("sql_ids.txt is updated")


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
rotating_handler = RotatingFileHandler(config['LOG_DIR'] + os.sep + 'update_sql_id.log',
                                       maxBytes=config['LOG_MAX_SIZE'],
                                       backupCount=config['LOG_MAX_FILES'])
formatter = logging.Formatter('[%(asctime)s] %(levelname)s : %(message)s')
rotating_handler.setFormatter(formatter)
root.addHandler(rotating_handler)

if config['DEBUG']:
    root.setLevel(logging.DEBUG)
else:
    root.setLevel(logging.INFO)

root.info('Service update_sql_id started')
root.info('Service update_sql_id configuration file: ' + config_file)
root.info('Service update_sql_id logs of reports: ' + config['LOG_DIR'])

# --------------------------------
#       Load configuration
# --------------------------------

path_log = config['LOG_DATA_DIR']
path_sql_id = config['SQL_ID_DATA_DIR']

# --------------------------------
#               Run
# --------------------------------

days_interval = 7
time_to_run = "03:00"
root.info('start updating sql_id.txt every ' + str(days_interval) + ' days at time ' + time_to_run)
# schedule.every(days_interval).days.at(time_to_run).do(save_sql_id_list, path_log, path_sql_id)

# example
schedule.every(1).minutes.at(":10").do(save_sql_id_list, path_log, path_sql_id)

while 1:
    schedule.run_pending()
    time.sleep(1)
