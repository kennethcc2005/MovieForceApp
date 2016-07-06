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
from collections import defaultdict
from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import urllib
import scipy

app = Flask(__name__)

# clf = joblib.load('my_movie_model20_v10.pkl')
moviefiles = np.load('data/feature_movie_name.npz')
modelfiles = np.load('data/my_movie_model20_10_array.npz')
valuefiles = np.load('data/my_movie_model20_10_value.npy')
with open('data/movie_dict.json', 'r') as f:
    movie_dict = json.load(f)
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

def next_guess_model(movie_features, user_answers, movie_dict):
    next_movie_list = []
    for i in xrange(len(movie_features)):
        true_list = []
        false_list = []
        temp = user_answers
        if temp[i] == 'TRUE': 
            temp[i] ='FALSE'
        else: temp[i] = 'TRUE'
        for k, v in enumerate(movie_features):
            if temp[k] == 'TRUE':
                true_list.append(v)
            else:
                false_list.append(v)
        for movie, features in movie_dict.iteritems():
            if (set(true_list).issubset(set(features))) and (not set(false_list).issubset(set(features))):
                next_movie_list.append(movie)
    newdict=defaultdict(list)
    print '11'
    for i in next_movie_list:
        newdict[i] = movie_dict[i]
    df = pd.DataFrame(columns = ['name','features','count'])
    ix = 0
    print '22'
    for k, v in newdict.items():
        if ix > 1000:
            continue
        for i in v:
            df.loc[ix] = [k,i,1]
            ix+=1
            
    print '33'
    df_new = df.pivot_table(values='count', index='name', columns='features', aggfunc='mean')
    df_new.fillna(0,inplace = True)
    clf = DecisionTreeClassifier('entropy',max_depth = 20)
    clf.fit(df_new.values,np.array(df_new.index))
    movie_list = df_new.index
    feature_list = df_new.columns.values
    X = df_new.columns.values
    np.save('X',X)
    tree_children_left = clf.tree_.children_left
    tree_children_right = clf.tree_.children_right
    tree_feature = clf.tree_.feature
    tree_threshold = clf.tree_.threshold
    tree_value = clf.tree_.value
    print '44'
    np.save('tree_children_left',tree_children_left)
    np.save('tree_children_right',tree_children_right)
    np.save('tree_feature',tree_feature)
    np.save('tree_threshold',tree_threshold)
    np.save('tree_value',tree_value)
    idx = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def searchMovie():
    search_tuple = process.extract(request.get_data(), choices, limit=5)
    result = [i[0] for i in search_tuple]
    return result

@app.route('/new_guess', methods = ['POST'])
def new_guess():
    movie_features = request.get_json()['movie_features'].split(',')
    user_answers = request.get_json()['user_answers'].split(',')
    print '1'
    try:
        next_guess_model(movie_features, user_answers, movie_dict)
    except:
        return jsonify({'status': 400, 'error': 'Oops, no more related movie found.'})
    question = 'Is this a movie about %s?' %(feature_list[0])
    # return render_template('movie.html',prediction=question)
    print '2'
    X = np.load('X.npy')
    tree_children_left1 = np.load('tree_children_left.npy')
    tree_children_right1 = np.load('tree_children_right.npy')
    tree_feature1 = np.load('tree_feature.npy')
    tree_threshold1 = np.load('tree_threshold.npy')
    tree_value1 = np.load('tree_value.npy')
    feature_idx, threshold, left_idx, right_idx = next_feature_threshold_left_right_child(0, tree_left = tree_children_left1, tree_right = tree_children_right1,\
                                            feature = tree_feature1, threshold = tree_threshold1)
    print 'newguess',feature_idx, threshold, left_idx, right_idx
    if X[feature_idx].isupper():
            question = 'Is this a movie about %s?' %(X[feature_idx])
    else: 
        question = question_type(X[feature_idx])
    return jsonify({'status':200, 'movie_feature': X[feature_idx],'question': question, 'left_idx': left_idx, 'right_idx': right_idx})        


@app.route('/movie_question', methods=['GET', 'POST'])
def movie_guess(X = feature_list, column_names = movie_list, idx = 0):
    if request.method == 'GET':
        feature_idx, threshold, left_idx, right_idx = next_feature_threshold_left_right_child(idx)
        prediction = X[feature_idx]
        question = 'Is this a movie about %s?' %(X[feature_idx])
        # user_questions.append(question)
        # user_keyword.append(feature_idx)
        return render_template('movie.html',prediction=question)

    if request.method == 'POST':
        return_answer = request.get_json()['answer']
        last_left_idx = request.get_json()['left_idx']
        last_right_idx = request.get_json()['right_idx']
        use_new_model = request.get_json()['use_new_model']
        
        if return_answer == 'TRUE':
            idx = last_right_idx
        else: 
            idx = last_left_idx
        if use_new_model == 'TRUE':
            X = np.load('X.npy')
            tree_children_left1 = np.load('tree_children_left.npy')
            tree_children_right1 = np.load('tree_children_right.npy')
            tree_feature1 = np.load('tree_feature.npy')
            tree_threshold1 = np.load('tree_threshold.npy')
            tree_value = np.load('tree_value.npy').tolist()
            feature_idx, threshold, updated_left_idx, updated_right_idx = next_feature_threshold_left_right_child(idx, tree_left = tree_children_left1, tree_right = tree_children_right1,\
                                            feature = tree_feature1, threshold = tree_threshold1)
        else:
            tree_children_left = modelfiles['arr_0']
            tree_children_right = modelfiles['arr_1']
            tree_feature = modelfiles['arr_2']
            tree_threshold = modelfiles['arr_3']
            tree_value = valuefiles.tolist().toarray()
            feature_idx, threshold, updated_left_idx, updated_right_idx = next_feature_threshold_left_right_child(idx)

        print feature_idx, threshold, updated_left_idx, updated_right_idx
        
        if feature_idx < 0:
            ans = tree_value[idx]
            #get the index array for the movie name index 
            print ans
            for index, n in enumerate(ans):
                if type(n) == list:
                    for i, v in enumerate(n):
                        if v == 1:
                            title = column_names[i].split('(')[0]
                            poster_url = movie_poster(title)
                            system_movie = column_names[i]
                            return jsonify({ 'my_guess': system_movie,'poster_url': poster_url})
                else:
                    if n == 1:
                        title = column_names[index].split('(')[0]
                        poster_url = movie_poster(title)
                        system_movie = column_names[index]
                        return jsonify({ 'my_guess': system_movie,'poster_url': poster_url})
        if X[feature_idx].isupper():
            question = 'Is this a movie about %s?' %(X[feature_idx])
        else: 
            question = question_type(X[feature_idx])
        return jsonify({ 'movie_feature': X[feature_idx],'question': question, 'left_idx': updated_left_idx, 'right_idx': updated_right_idx}) 


if __name__ == '__main__':
    # Register for pinging service

    # Start Flask app
    app.run(debug=True)
