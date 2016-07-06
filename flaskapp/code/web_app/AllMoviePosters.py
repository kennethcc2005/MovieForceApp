from flask import Flask, request, render_template, jsonify
import json
import requests
import socket
import time
from datetime import datetime
import numpy as np 
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from MoviePosters import MoviePosters
import urllib
import string

moviefiles = np.load('../../data/feature_movie_name.npz')
movie_list = moviefiles['arr_0']
exclude = set(string.punctuation)

def movie_poster(title):
    req = MoviePosters()
    url = req.imdb_id_from_title(title)
    print url
    if url == None:
        return 0
    poster_url = req.get_poster_url()     
    return poster_url

def all_posters(save_path, movie_list = movie_list):
    posters_url = []
    i =0 
    for name in movie_list[:1000]:
        i += 1
        title = name.split('(')[-2].replace(r")","")
        title = ''.join(ch for ch in title if ch not in exclude)
        poster_url = movie_poster(title)
        posters_url.append(poster_url)
        if i % 100 == 0: 
            print "Url #%i" %(i)
            np.save('../../data/movie_posters_url%i' %(i), posters_url)
    posters_url = np.array(posters_url)
    np.save(save_path, posters_url)

if __name__ == '__main__':
    all_posters(save_path = '../../data/movie_posters_url',movie_list = movie_list)