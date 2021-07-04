from flask import Flask, render_template
from flask import request
import json
import plotly
from flask_cors import CORS

from data_processing import preprocessing, system_fault

app = Flask(__name__)
CORS(app)


@app.route('/get_sql_ids')
def get_sql_id_list():
    path = "C://Users//DM3522//Desktop//access.log"
    sql_id_list = preprocessing.get_sql_id_list(150, path)
    graphJSON = json.dumps(sql_id_list)

    return graphJSON


@app.route('/plot', methods=['GET'])
def plot_sys_fault():
    sql_id = request.args.get('sql_id', None)
    days_num = request.args.get('days_num', None)

    path = "C://Users//DM3522//Desktop//access.log"
    sql_stores_dict = preprocessing.get_preprocessed_data(days=days_num, path_file=path)
    if len(sql_stores_dict) == 0 or sql_id not in sql_stores_dict.keys():
        return 'Data is not available in the specified days. Please increase the days number', 400

    # fig = creat_fig(int(sql_id), int(days_num))
    fig = creat_fig(sql_stores_dict, int(sql_id))
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graph_json


@app.route('/')
def home():
    return render_template('sys-fault.html')


def creat_fig(sql_stores_dict, sql_id):
    # get the data dictionary
    # sql_stores_dict = preprocessing.get_preprocessed_data(days=days_num, path_file=path)

    # group the data based on the defined time interval
    grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=10)

    # detect the fault time intervals in the system
    sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=0.9, min_valid_pair_intervals=10)

    # show the graph on moving average
    moved_average = preprocessing.moving_average(sql_stores_dict[sql_id], window_size=500)

    return system_fault.plot_sys_fault(moved_average, sql_id, sys_fault)

# @app.errorhandler(Exception)
# def handle_exception(e):
#     if e.args[0] == 'Data is not available':
#         return 'Data is not available in the specified days. Please increase the days number', 400
#     else:
#         return 'internal server error', 500

# 102588
# 102586
# 102587
