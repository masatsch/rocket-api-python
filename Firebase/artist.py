import pandas as pd
import numpy as np
import requests
import re
import json
import time
import datetime
import subprocess
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# from firebase_admin import storage
from google.cloud import storage
import uuid

def getArtists():
    print("アーティスト情報を取得します", end="")
    artists_ref = db.collection(u'artists')
    docs = artists_ref.stream()
    artists = pd.DataFrame({"id": [], "artistName": [], "genre": [], "members": [], "biography": [], "homepageUrl": [], "twitterUrl": [], "avatarUrl": [], "lastUpdate": [], "favoriteUsers": []})
    for doc in docs:
        print(".", end="")
        data = doc.to_dict()
        artist = pd.Series([doc.id, data["artistName"], data["genre"], data["members"], data["biography"], data["homepageUrl"], data["twitterUrl"], data["avatarUrl"], data["lastUpdate"], data["favoriteUsers"]], index=["id", "artistName", "genre", "members", "biography", "homepageUrl", "twitterUrl", "avatarUrl", "lastUpdate", "favoriteUsers"])
        artists = artists.append(artist, ignore_index=True)

    print()
    print("OK")
    print()

    return artists

def updateArtist(id, data):
    ref = db.collection(u'artists').document(id)
    ref.update(data)

def registerArtists():
    result = subprocess.run(['rm', '-rf', '../assets'])
    result = subprocess.run(['wget', '-O', 'newArtists.xlsx', 'https://docs.google.com/spreadsheets/d/1lgg1_VzzKXYWxwiWHHhzuwhc4eKye2g2QbjyjYMI580/export?gid=0&format=xlsx'])
    print(result)

    artists = pd.read_excel("newArtists.xlsx")
    for key, artist in artistlist.iterrows():
        try:
            member = json.loads(artist["member"])
        except:
            print("failed to parse member. The artist is: {}".format(artist["artistName"]))
            continue
        
        r = requests.get(artist["jacketImageUrl"])
        image = r.content
        with open("../assets/{}.jpg".format(artist["artistName"]), "wb") as f:
            f.write(image)
        
        if artist["registered"]:
            item = {
                "artistName": artist["artistName"],
                "biography": artist["biography"],
                "genre": artist["genre"],
                "homepageUrl": artist["homepageUrl"],
                "members": member,
                "twitterUrl": artist["twitterUrl"],
                "sourceUrl": artist["jacketImageUrl"]
            }

            docs = db.collection(u'artists').where(u'artistName', u'==', artist["artistName"]).stream()
            for doc in docs:
                db.collection(u'artists').document(doc.id).update(item)
                
            continue

    item = {
        "artistName": artist["artistName"],
        "avatarUrl": "yet",
        "biography": artist["biography"],
        "favoriteUsers": [],
        "genre": artist["genre"],
        "homepageUrl": artist["homepageUrl"],
        "lastUpdateDate": datetime.datetime.now(),
        "members": member,
        "sourceUrl": artist["jacketImageUrl"],
        "twitterUrl": artist["twitterUrl"],
    }
    
    db.collection(u'artists').document().set(item)


if __name__ == '__main__':
    cred = credentials.Certificate('livehouse-262123-0b1410885e83.json')
    firebase_admin.initialize_app(cred)
    storage_client = storage.Client.from_service_account_json('livehouse-262123-0b1410885e83.json')
    db = firestore.client()

    artists = getArtists()
    artists.to_excel('../firebase_artists.xlsx')