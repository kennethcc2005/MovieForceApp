'''
Movie keyword and genres data is from IMDB.
Information courtesy of
IMDb
(http://www.imdb.com).
Used with permission.
Data link: ftp://ftp.fu-berlin.de/pub/misc/movies/database/
'''
import pandas as pd
import numpy as np
import csv
# import graphlab
import os
from collections import defaultdict
from sklearn.tree import DecisionTreeClassifier
from sklearn.externals import joblib
# class MovieCleanData(object):

#Need to clean up the list before data preprocessing.
def movie_keyword(keyword_file = '../data/keywords_clean.list', pickle_path = '../data/df_key'):    
    df_key = pd.read_csv(keyword_file, delimiter='\n',header = None)
    df_key['Movie'] = [df_key[0][i].split('\t')[0] for i in xrange(df_key.shape[0])]
    df_key['Keyword'] = [df_key[0][i].split('\t')[-1] for i in xrange(df_key.shape[0])]
    # df_key.to_pickle(pickle_path)
    return df_key

#If the dataframe has error, need to cleanup the list file manually.
#Return a pivot dataframe with 27 movie genres. 
def movie_genres(genres_file = '../data/genres.list',pickle_path = '../data/df_genres_pivot'):
    df_genres = pd.read_csv(genres_file,delimiter= '\t', dtype = 'str', header = None)
    df_genres['Genres'] = pd.concat([df_genres[6].dropna(),df_genres[5].dropna(),\
                            df_genres[4].dropna(),df_genres[3].dropna(),df_genres[2].dropna(),\
                            df_genres[1].dropna()]).reindex_like(df_genres)
    df_genres.drop([1,2,3,4,5,6],axis = 1,inplace = True)
    df_genres.columns = ['idx','Genres']
    df_genres['cnt'] = 1
    df_genres_pivot = df_genres.pivot_table(values = 'cnt', index = 'idx', columns = 'Genres')
    # df_genres_pivot.to_pickle(pickle_path)
    return df_genres_pivot

#The list file includes votes and rates for each movie; need to clean up the data manually.
#Return DafaFrame with vote number greater 10000.
def movie_rating(rating_file = '../data/ratings.list', min_vote_cnt = 10000):
    df_rating = pd.read_csv(rating_file, delimiter='\t', dtype='unicode')
    df_rating['Votes'] =  [int([i for i in df_rating.loc[j][0].split(' ') if i != ''][1]) \
                            for j in xrange(df_rating.shape[0])]
    df_rating['Movie'] = [df_rating['New  Distribution  Votes  Rank  Title'][i][32:] \
                            for i in xrange(len(df_rating))]

    #Exclude the tv dramas in dataframe.
    df_tv = df_rating[df_rating.Movie.str.startswith('"')]
    df_movie_rating = df_rating.drop(df_tv.index)
    df_popular_movie = df_movie_rating[df_movie_rating.Votes > min_vote_cnt]
    l = df_popular_movie.Movie
    df_popular_movie.Movie = [i if i[0] != ' ' else i[1:] for i in l]
    df_popular_movie = df_popular_movie.set_index(df_popular_movie.Movie)
    # df_popular_movie.to_pickle('../data/df_popular_movie_10000')
    return df_popular_movie

def movie_genres_rating(df_movie_genres, df_movie_rating): 
    df_gen_vote = df_movie_rating.join(df_movie_genres)
    df_gen_vote.drop(['New  Distribution  Votes  Rank  Title','Movie','_ Drama<>Mystery<>crime_'],axis = 1,inplace=True)
    # df_gen_vote.to_pickle('../data/df_gen_vote')
    return df_gen_vote
    
def movie_force_data(df_key, df_gen_vote, number_keywords = 100):
    df_clean_long = df_key.set_index(df_key.Movie).ix[df_gen_vote.index]
    df = df_clean_long.ix[df_gen_vote.index[0]][:number_keywords]
    for movie in df_gen_vote.index[1:]:
        df = pd.concat([df,df_clean_long.ix[movie][:number_keywords]],axis =0)
    df['count'] = 1
    df100 = df[['Movie','Keyword','count']]
    df100 = df100.pivot_table(values='count', index='Movie', columns='Keyword')
    df_100key_genres = df100.join(df_gen_vote)
    df_100key_genres.pop('Votes')
    df_100key_genres = df_100key_genres.fillna(0)
    # df_100key_genres.to_pickle('../data/df_100key_genres')
    return df_100key_genres

def movie_dict(df_100key_genres, json_path = '../data/movie_dict.json'):
    movie_dict = defaultdict(list)
    for movie in df_100key_genres.index.values:
        for keyword,value in df_100key_genres.loc[movie].iteritems():
            if value == 1:
                movie_dict[movie].append(keyword)
    with open(json_path, 'w') as f:
        json.dump(movie_dict, f)

def movie_model(df_100key_genres, max_depth = 20, pickle_path = '../data/my_movie_model20_v10.pkl'):
    X = df_100key_genres.values
    y = df_100key_genres.index
    clf = DecisionTreeClassifier('entropy',max_depth = max_depth)
    clf.fit(X,y)
    # clf.score(X,y)
    # joblib.dump(clf, pickle_path)
    return clf

def save_feature_movie_name(df_100key_genres, save_path = '../data/feature_movie_name'):
    movie_list = df_100key_genres.index
    feature_list = df_100key_genres.columns.values
    np.savez(save_path,movie_list,feature_list)

def save_model_features(clf,save_path = '../data/my_movie_model20_10_array'):
    np.savez(save_path,clf.tree_.children_left,clf.tree_.children_right,clf.tree_.feature,clf.tree_.threshold)

def save_model_value(clf, save_path = '../data/my_movie_model20_10_value'):
    valuefiles = clf.tree_.value
    sparse_values = sparse.lil_matrix(valuefiles.astype(int))
    np.save(save_path,sparse_values)

if __name__ == '__main__':
    df_popular_movie = movie_rating(rating_file = '../data/ratings.list', min_vote_cnt = 10000)
    df_genres_pivot = movie_genres(genres_file = '../data/genres.list',pickle_path = '../data/df_genres_pivot')
    df_gen_vote = movie_genres_rating(df_movie_genres = df_genres_pivot, df_movie_rating = df_popular_movie)
    df_key = movie_keyword(keyword_file = '../data/keywords_clean.list', pickle_path = '../data/df_key')
    df_100key_genres = movie_force_data(df_key = df_key, df_gen_vote = df_gen_vote, number_keywords = 100)
    movie_dict(df_100key_genres, json_path = '../data/movie_dict.json')
    clf = movie_model(df_100key_genres = df_100key_genres, max_depth = 20, pickle_path = '../data/my_movie_model20_v10.pkl')
    save_feature_movie_name(df_100key_genres = df_100key_genres)
    save_model_features(clf = clf)
    save_model_value(clf = clf)


