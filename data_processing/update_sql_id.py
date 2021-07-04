import datetime
from threading import Timer


def save_sql_id_list(path_file):
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(days=days)

    file = open(path_file)
    lines = file.read().splitlines()
    data = []

    # we start iterating from end to be able to break the for loop. Better performance
    for line in reversed(lines):
        data_line = line.split()
        line_date = data_line[3].replace('[', '').replace(':', ' ', 1)
        line_date = datetime.datetime.strptime(line_date, '%d/%b/%Y %H:%M:%S')

        # break if the line_date exceeded the request date
        if line_date < start_time:
            break

        # some data do not have sql_id
        if "sqlstore_id" in line:
            sql_id = data_line[6].split("sqlstore_id=")[1].split("&")[0]
            if int(sql_id) not in data:
                data.append(int(sql_id))

    return data


path = "C://Users//DM3522//Desktop//access.log"
secs = 10
t = Timer(secs, save_sql_id_list, [path])
t.start()
