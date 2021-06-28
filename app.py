from flask import Flask, render_template
from flask import request, jsonify
import json
import plotly
import os
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

    fig = creat_fig(int(sql_id), int(days_num))
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON
    # return render_template('sys-fault.html', graphJSON=graphJSON)


def creat_fig(sql_id, days_num):
    # dirname = os.path.dirname(__file__)
    # path_file = os.path.join(dirname, '../resources/access.log')
    path = "C://Users//DM3522//Desktop//access.log"

    # get the data dictionary
    sql_stores_dict = preprocessing.get_preprocessed_data(days=days_num, path_file=path)
    assert len(sql_stores_dict[sql_id][0]) != 0, 'Data is not available'

    grouped_data = system_fault.group_by_minutes(sql_stores_dict, time_interval=10)
    sys_fault = system_fault.calculate_fault(grouped_data, acceptance_rate=0.9, min_valid_pair_intervals=10)

    # show the graph on moving average
    moved_average = preprocessing.moving_average(sql_stores_dict[sql_id], window_size=500)

    return system_fault.plot_sys_fault(moved_average, sql_id, sys_fault)

# @app.errorhandler(Exception)
# def handle_exception(e):
#     return 'bad request!', 400
