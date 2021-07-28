from getopt import getopt, GetoptError
import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler


def save_sql_id_list(path_dir, path_sqls):
    root.debug("start updating the sql_ids.txt")

    sql_id_file = open(path_sqls, "w")
    try:
        # Change the directory
        os.chdir(path_dir)
    except Exception as e:
        root.error(e, exc_info=True)
        print("There is not such file or directory!")
        exit(-1)

    data = []
    if len(os.listdir()) == 0:
        root.warning("There is not any log file to be processed")

    # iterate through all file
    with sql_id_file as file_save:
        for file_log in os.listdir():
            # Check whether file is in text format or not
            if file_log.endswith(".txt"):
                file_path = path_dir + os.sep + file_log
                file = open(file_path)
                lines = file.read().splitlines()

                # we start iterating from end to be able to break the for loop. Better performance
                for line in lines:
                    # some data do not have sql_id
                    if "sqlstore_id" in line:
                        data_line = line.split()

                        if len(data_line) == 10:
                            status_index = 8
                            sql_id_index = 6

                        else:
                            status_index = 7
                            sql_id_index = 5

                        if data_line[status_index] == '200':
                            sql_id = data_line[sql_id_index].split("sqlstore_id=")[1].split("&")[0]
                            # some data do not have response time and some of them have error
                            if sql_id != 'null' and int(sql_id) not in data:
                                data.append(int(sql_id))
                                file_save.write(sql_id + "\n")

                file.close()
            else:
                logging.warning("Log file is not in the .txt format")

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
root.info('start updating sql_id.txt')
save_sql_id_list(path_log, path_sql_id)
