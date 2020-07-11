import pandas as pd
import numpy as np
import requests
import re
import json
import time
import datetime
import firebase_admin
from bs4 import BeautifulSoup
from firebase_admin import credentials
from firebase_admin import firestore
# from firebase_admin import storage
from google.cloud import storage
import uuid


# Use a service account
cred = credentials.Certificate('auth.json')
firebase_admin.initialize_app(cred)
storage_client = storage.Client.from_service_account_json('auth.json')
db = firestore.client()

class Itunes:
    
    def getSongs(self, artist: str):
        print("アーティストの楽曲を取得します")
        artist_re = re.sub(" ", "+", artist)
        url = "http://itunes.apple.com/search?term={}&country=JP&lang=ja_jp&media=music&entity=song&attribute=artistTerm&limit=2000".format(artist_re)
        response = requests.get(url)
        response_body = json.loads(response.text)
        
        artistId = []
        collectionId = []
        trackId = []
        artistName = []
        collectionName = []
        trackName = []
        collectionCensoredName = []
        trackCensoredName = []
        artistViewUrl = []
        collectionViewUrl = []
        trackViewUrl = []
        previewUrl = []
        artworkUrl = []
        releaseDate = []
        primaryGenreName = []
        
        for song in response_body["results"]:

            artistId.append(str(song["artistId"]))    
            collectionId.append(str(song["collectionId"]))
            trackId.append(str(song["trackId"]))
            artistName.append(song["artistName"])
            collectionName.append(song["collectionName"])
            trackName.append(song["trackName"])
            collectionCensoredName.append(song["collectionCensoredName"])
            trackCensoredName.append(song["trackCensoredName"])
            try:
                artistViewUrl.append(song["artistViewUrl"])
            except:
                artistViewUrl.append(None)
                
            try:
                collectionViewUrl.append(song["collectionViewUrl"])                
            except:
                collectionViewUrl.append(None)

            try:
                trackViewUrl.append(song["trackViewUrl"])
            except:
                trackViewUrl.append(None)
            
            try:
                previewUrl.append(song["previewUrl"])
            except:
                previewUrl.append(None)
            
            try:
                artworkUrl.append(song["artworkUrl60"])
            except:
                artworkUrl.append(None)
                
            releaseDate.append(datetime.datetime.strptime(song["releaseDate"], '%Y-%m-%dT%H:%M:%SZ'))
            primaryGenreName.append(song["primaryGenreName"])
            
        df = pd.DataFrame({
            "artistId": artistId,
            "collectionId": collectionId,
            "trackId": trackId,
            "artistName": artistName,
            "collectionName": collectionName,
            "trackName": trackName,
            "collectionCensoredName": collectionCensoredName,
            "trackCensoredName": trackCensoredName,
            "artistViewUrl": artistViewUrl,
            "collectionViewUrl": collectionViewUrl,
            "trackViewUrl": trackViewUrl,
            "previewUrl": previewUrl,
            "artworkUrl": artworkUrl,
            "releaseDate": releaseDate,
            "primaryGenreName": primaryGenreName
        })
        return df

if __name__ == '__main__':
    itunes = Itunes()
    artists = pd.read_excel("../firebase_artists.xlsx")
    itunes_songs_df = pd.DataFrame({
                "artistId": [],
                "collectionId": [],
                "trackId": [],
                "artistName": [],
                "collectionName": [],
                "trackName": [],
                "collectionCensoredName": [],
                "trackCensoredName": [],
                "artistViewUrl": [],
                "collectionViewUrl": [],
                "trackViewUrl": [],
                "previewUrl": [],
                "artworkUrl": [],
                "releaseDate": [],
                "primaryGenreName": []
            })

    for artist in artists.artistName.values:
        songs = itunes.getSongs(artist)
        itunes_songs_df = pd.concat([itunes_songs_df, songs])
    
    itunes_songs_df.to_excel("../itunes_songs.xlsx")