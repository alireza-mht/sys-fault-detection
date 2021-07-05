import time
from threading import Timer
import schedule
import datetime


def save_sql_id_list(path_file):
    print("start")
    print(datetime.datetime.now())
    file = open(path_file)
    lines = file.read().splitlines()
    data = []
    with open("../resources/sql_ids.txt", "w") as file_save:
        # we start iterating from end to be able to break the for loop. Better performance
        for line in reversed(lines):
            data_line = line.split()

            # some data do not have sql_id
            if "sqlstore_id" in line:
                sql_id = data_line[6].split("sqlstore_id=")[1].split("&")[0]
                if sql_id != "null" and int(sql_id) not in data:
                    data.append(int(sql_id))
                    file_save.write(sql_id + "\n")
    print("finish")
    print(datetime.datetime.now())


path = "C:/Users/DM3522/Desktop/access.log"
secs = 20
# schedule.every().sunday.at('1:00').do(save_sql_id_list, path)
schedule.every().minute.at(":10").do(save_sql_id_list, path)
while 1:
    schedule.run_pending()
    time.sleep(1)
