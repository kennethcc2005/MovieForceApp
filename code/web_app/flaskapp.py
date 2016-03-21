from flask import Flask, request, render_template, jsonify
import json
import requests
import socket
import time
from datetime import datetime
import numpy as np 
# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process
from MoviePosters import MoviePosters
import urllib

app = Flask(__name__)
PORT = 5353
DATA = []
TIMESTAMP = []

# clf = joblib.load('my_movie_model20_v10.pkl')
moviefiles = np.load('data/feature_movie_name.npz')
modelfiles = np.load('data/my_movie_model20_10_array.npz')
valuefiles = np.load('data/my_movie_model20_10_value.npy')

feature_list = moviefiles['arr_1']
movie_list = moviefiles['arr_0']

tree_children_left = modelfiles['arr_0']
tree_children_right = modelfiles['arr_1']
tree_feature = modelfiles['arr_2']
tree_threshold = modelfiles['arr_3']
tree_value = valuefiles.tolist().toarray()

def fuzzy_search(user_search):
    search_tuple = process.extract(user_search, choices, limit=5)
    result = [i[0] for i in search_tuple]
    return result

def movie_poster(title):
    req = MoviePosters()
    req.imdb_id_from_title(title)
    poster_url = req.get_poster_url()     
    return poster_url

def question_type(X):
    idx = np.random.randint(0,3)
    question1 = 'Is this a movie about %s?' %(X)
    question2 = 'I think this movie talks about %s.' %(X)
    question3 = 'Hmmm, does this movie has the element of %s?'%(X)
    question_list = [question1,question2,question3]
    return question_list[idx]

def next_feature_threshold_left_right_child(current_idx, tree_left = tree_children_left, tree_right = tree_children_right,\
                                            feature = tree_feature, threshold = tree_threshold):
    left_idx = tree_left[current_idx]
    right_idx = tree_right[current_idx]
    feature_idx = feature[current_idx]
    threshold = threshold[current_idx]
    return feature_idx, threshold, left_idx, right_idx

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/search', methods=['POST'])
# def searchMovie():
    #  => ''
    # search_tuple = process.extract(request.get_data(), choices, limit=5)
    # result = [i[0] for i in search_tuple]
    # return result


@app.route('/movie_question', methods=['GET', 'POST'])
def movie_guess(X = feature_list, column_names = movie_list, idx = 0):
    user_questions = []
    user_answers = []
    user_keyword = []
    feature_idx, threshold, left_idx, right_idx = next_feature_threshold_left_right_child(idx)

    if request.method == 'GET':
        prediction = X[feature_idx]
        question = 'Is this a movie about %s?' %(X[feature_idx])
        user_questions.append(question)
        user_keyword.append(feature_idx)
        return render_template('movie.html',prediction=question)

    if request.method == 'POST':
        return_answer = request.get_json()['answer']
        last_left_idx = request.get_json()['left_idx']
        last_right_idx = request.get_json()['right_idx']
        if return_answer == 'TRUE':
            idx = last_right_idx
            user_answers.append('TRUE')
        else: 
            idx = last_left_idx
            user_answers.append('FALSE')

        feature_idx, threshold, updated_left_idx, updated_right_idx = next_feature_threshold_left_right_child(idx)
        
        # if sum(ans) == 1:
        if feature_idx < 0:
            ans = tree_value[idx]
            #get the index array for the movie name index 
            print ans
            for index, n in enumerate(ans):
                if n == 1:
                    title = column_names[index].split('(')[0]
                    poster_url = movie_poster(title)
                    system_movie = column_names[index]
                    print poster_url
                    return jsonify({ 'my_guess': system_movie,'poster_url': poster_url})
            # column_names[index]
        if X[feature_idx].isupper():
            question = 'Is this a movie about %s?' %(X[feature_idx])
        else: 
            question = question_type(X[feature_idx])
        user_questions.append(question)
        user_keyword.append(feature_idx)

        return jsonify({ 'question': question, 'left_idx': updated_left_idx, 'right_idx': updated_right_idx})        

# @app.route('/movie_features', methods=['GET', 'POST'])
# def movie_features(system_movie, user_movie, idx):
#     if request.method == 'GET':
#         prediction = X[feature_idx]
#         question = 'Is this a movie about %s?' %(X[feature_idx])
#         return render_template('movie.html',prediction=question)    


if __name__ == '__main__':
    # Register for pinging service

    # Start Flask app
    app.run(host='0.0.0.0', port=PORT, debug=True)
