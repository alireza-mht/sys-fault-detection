# sys-fault-detection

***
This project tris to find the system faults of system by considering the increments in response time of sql_ids.

### How does it work?

***
It groups all the data into 10 minutes and makes an average of data in each time interval. Then it checks the behaviour
of average response times in all the time intervals of all sql_ids. It observes the increments by comparing the average
response time in two side by side 10 minutes intervals for each sql_id. First, it checks if there is data in the
intervals, and if there is data in both the side-by-side interval, it would mark the increment. All the intervals that
have data are considered valid intervals. We define a variable as an acceptance rate for available sql_ids. If the
number of increments for two side-by-side intervals is more than the acceptance rate multiplied by the number of valid
side-by-side intervals, we can say that there is a system fault in that specific time interval.


### Main parameters
***
The parameters in the project:

- `sql_id`: this parameter defines the id of sql request
- `days_num`: it helps to show the data of last specific days

- `path_file`: the default path for the log file is in the resources folder. it can be changed by specifying this variable

- `time_interval`: group all the data into specific time interval. Default value is 10 minutes.
- `acceptance_rate`: a threshold for accepting the fault detection. if we decrease the value, the number of faults will
  be increased. this variable multiplied by `valid_pair_intervals` variable will generate the minimum number of
  increments for considering two intervals as the fault.
- `min_valid_pair_intervals`: two pair intervals are defined as the side-by-side intervals. we called them valid if we
  have data in both of the intervals. this variable specifies the minimum number of valid pair intervals which is
  required for the system fault detection

- `windows_size`: to have a better graph we calculate the moving average, and we show it with the plotly. this variable
defines the windows size of moving average

### How to work with it?
***
By running of this project, you can see the figure of each sql_id with its system fault. So the requests should contain
two parameters:

Example of requesting the figures:

```
  http://127.0.0.1:5000/test?sql_id=143&days_num=150
```

Result:

![](resources/running_example.png)
