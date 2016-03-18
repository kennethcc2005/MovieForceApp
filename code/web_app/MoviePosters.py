import requests
import json
import urllib

class  MoviePosters(object):
    """docstring for  MoviePosters"""
    def __init__(self, key = '97435aa0b3279f548f2eb1591765c978',\
                    base_url =  "http://image.tmdb.org/t/p/",\
                    max_size = 'original'):
        self.key = key
        self.base_url = base_url
        self.max_size = max_size
        self.imdbid = 0

    def imdb_id_from_title(self,title):
        """ return IMDB id for search string

            Args::
                title (str): the movie title search string

            Returns: 
                str. IMDB id, e.g., 'tt0095016' 
                None. If no match was found

        """
        pattern = 'http://www.imdb.com/xml/find?json=1&nr=1&tt=on&q={movie_title}'
        url = pattern.format(movie_title=urllib.quote(title))
        r = requests.get(url)
        res = r.json()
        # sections in descending order or preference
        for section in ['popular','exact','substring']:
            key = 'title_' + section 
            if key in res:
                self.imdbid = res[key][0]['id']
                return res[key][0]['id']


    def get_poster_url(self):
        IMG_PATTERN = 'http://api.themoviedb.org/3/movie/{imdbid}/images?api_key={key}'
        r = requests.get(IMG_PATTERN.format(key=self.key,imdbid=self.imdbid))
        api_response = r.json()
        # if api_response['status_code'] == 34:
        #     return 0 
        try: 
            posters = api_response['posters']
            # poster_urls = []
            # for poster in posters:
            rel_path = posters[0]['file_path']
            url = "{0}{1}{2}".format(self.base_url, self.max_size, rel_path)
            return url
        except IndexError:
            return 0 
        except KeyError:
            return 0 