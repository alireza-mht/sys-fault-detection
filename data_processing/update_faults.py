import time
import schedule
import datetime
from data_processing import preprocessing, system_fault, fault_database


def update_faults(path_log, path_fault, interval, rate, min_valid_pair):
    if fault_database.is_valid_database(time_interval, rate, min_valid_pair, path_fault):

        time_now = datetime.datetime.now()
        last_update = fault_database.get_last_update(path_fault)
        last_update_datetime = datetime.datetime.strptime(last_update, '%Y/%m/%d-%H:%M:%S')
        time_delta = time_now - last_update_datetime
        time_delta = time_delta.days
    else:
        time_now = datetime.datetime.now()
        last_update_datetime = preprocessing.get_first_start_time(path_log)
        time_delta = time_now - last_update_datetime
        time_delta = time_delta.days - 1
        fault_database.creat_database(time_interval, rate, min_valid_pair, time_now, path_fault)

    sql_stores_dict = preprocessing.get_preprocessed_data(days=time_delta + 1, path_file=path_log)
    grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=interval)
    sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=rate,
                                             min_valid_pair_intervals=min_valid_pair)

    fault_database.write_new_faults(time_now, sys_fault, path=path_fault)



path_log = "C:/Users/DM3522/Desktop/access.log"
path_fault = "../resources/faults.txt"
time_interval = 10
acceptance_rate = 0.9
min_valid_pair_intervals = 10
days_interval = 1
time_to_run = "03:00"
# schedule.every(days_interval).days.at(time_to_run).do(update_faults, path, time_interval, acceptance_rate,
#                                                       min_valid_pair_intervals)
# schedule.every(20).seconds.do(update_faults, path_log, path_fault, time_interval, acceptance_rate,
#                               min_valid_pair_intervals)

# example
# schedule.every(3).minutes.at(":10").do(save_sql_id_list, path)

# while 1:
#     schedule.run_pending()
#     time.sleep(1)
update_faults(path_log, path_fault, time_interval, acceptance_rate, min_valid_pair_intervals)
