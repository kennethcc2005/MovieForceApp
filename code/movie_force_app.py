from flask import Flask, request, render_template
import json
import requests
import socket
import time
from datetime import datetime

app = Flask(__name__)
PORT = 5353
DATA = []
TIMESTAMP = []
# clf = joblib.load('my_movie_model20_v10.pkl')
moviefiles = np.load('../data/feature_movie_name.npz')
modelfiles = np.load('../data/my_movie_model20_10_array.npz')
valuefiles = np.load('../data/my_movie_model20_10_value.npy')

feature_list = moviefiles['arr_1']
movie_list = moviefiles['arr_0']

tree_children_left = modelfiles['arr_0']
tree_children_right = modelfiles['arr_1']
tree_feature = modelfiles['arr_2']
tree_threshold = modelfiles['arr_3']
tree_value = valuefiles.tolist().toarray()

def next_feature_threshold_left_right_child(current_idx, tree_left = tree_children_left, tree_right = tree_children_right,\
                                            feature = tree_feature, threshold = tree_threshold):
    left_idx = tree_left[current_idx]
    right_idx = tree_right[current_idx]
    feature_idx = feature[current_idx]
    threshold = threshold[current_idx]
    return feature_idx, threshold, left_idx, right_idx

def movie_guess(X = feature_list, column_names = movie_list, idx = 0):
    ''' Compute the expected gain from splitting the data along all possible
       values of feature. '''
    feature_idx, threshold, left_idx, right_idx = next_feature_threshold_left_right_child(idx)
    ans = tree_value[idx]
    if sum(ans) <= 10:
        for index, n in enumerate(ans):
            if n == 1: print column_names[index]
        if feature_idx < 0: 
            return 'DONE'
        print 'Keep going! The machine has', int(sum(ans)), 'movies left'
        print 'Is the movie has the element of %s [True/False]:' %(X[feature_idx])
    else:
        print 'Is the movie has the element of %s [True/False]:' %(X[feature_idx])
    user_input = str(raw_input())
    if user_input == 'F':
        idx = left_idx
    elif user_input == 'T':
        idx = right_idx
    else: print'errrrrror'
    return movie_guess(X, column_names, idx = idx)

@app.route('/score', methods=['POST'])
def score():
    DATA.append(json.dumps(request.json, sort_keys=True, indent=4, separators=(',', ': ')))
    TIMESTAMP.append(time.time())
    return ""


@app.route('/check')
def check():
    line1 = "Number of data points: {0}".format(len(DATA))
    if DATA and TIMESTAMP:
        dt = datetime.fromtimestamp(TIMESTAMP[-1])
        data_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        line2 = "Latest datapoint received at: {0}".format(data_time)
        line3 = DATA[-1]
        output = "{0}\n\n{1}\n\n{2}".format(line1, line2, line3)
    else:
        output = line1
    return output, 200, {'Content-Type': 'text/css; charset=utf-8'}

def register_for_ping(ip, port):
    registration_data = {'ip': ip, 'port': port}
    requests.post(REGISTER_URL, data=registration_data)

if __name__ == '__main__':
    # Register for pinging service
    ip_address = socket.gethostbyname(socket.gethostname())
    register_for_ping(ip_address, str(PORT))

    # Start Flask app
    app.run(host='0.0.0.0', port=PORT, debug=True)
