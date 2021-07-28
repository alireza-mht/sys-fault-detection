import datetime
import logging


def is_valid_database(time_interval, acceptance_rate, min_valid_pair_intervals, path):
    logging.debug("check database validation")

    file = open(path)
    lines = file.read().splitlines()
    file.close()

    if (len(lines) > 2 and lines[1].split(" ")[1] == str(acceptance_rate) and lines[2].split(" ")[1] == str(
            time_interval)
            and lines[3].split(" ")[1] == str(min_valid_pair_intervals)):
        return True


def creat_database(time_interval, acceptance_rate, min_valid_pair_intervals, time, path):
    headers = ["last_update: " + time.strftime('%Y/%m/%d-%H:%M:%S') + "\n",
               "acceptance_rate: " + str(acceptance_rate) + "\n",
               "time_intervals: " + str(time_interval) + "\n",
               "min_valid_accepted_interval: " + str(min_valid_pair_intervals) + "\n"]
    file = open(path, "w")
    file.writelines(headers)
    file.close()


def write_new_faults(last_update, sys_faults, path):
    file = open(path, "r")
    list_of_lines = file.readlines()
    list_of_lines[0] = "last_update: " + last_update.strftime('%Y/%m/%d-%H:%M:%S') + "\n"
    file.close()

    for i in range(len(sys_faults)):
        list_of_lines.append(sys_faults[i][0]
                             .strftime('%Y/%m/%d-%H:%M:%S') + "," +
                             sys_faults[i][1]
                             .strftime('%Y/%m/%d-%H:%M:%S') + "\n")
    file = open(path, "w")
    file.writelines(list_of_lines)
    file.close()


def get_saved_faults(path):
    file = open(path, "r")
    list_of_lines = file.read().splitlines()
    fault_pair_time_intervals = []
    for line in list_of_lines[4:]:
        interval_one = datetime.datetime.strptime(line.split(",")[0], '%Y/%m/%d-%H:%M:%S')
        interval_two = datetime.datetime.strptime(line.split(",")[1], '%Y/%m/%d-%H:%M:%S')
        fault_pair_time_intervals.append((interval_one, interval_two))
    return fault_pair_time_intervals


def get_last_update(path):
    file = open(path, "r")
    list_of_lines = file.read().splitlines()
    update_time = list_of_lines[0].split(" ")[1]
    return update_time
