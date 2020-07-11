import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import json
import datetime
import uuid

class LiveFans:

    def searchArtist(self, aritstName: str):
        url = "https://www.livefans.jp/search?option=6&keyword={}&genre=all".format(artistName)
        r = requests.get(url)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        res = soup.find("div", attrs={"class": "artistBox"}).find("a").get("href")
        return res

    def getConcerts(self, url: str, last_update, is_next_page=False, concerts=[]):
        if not is_next_page:
            print("コンサート情報を入手します.", end="")
            url = "/search" + url
           
        print("url: {}".format(url))    
        r = requests.get("https://www.livefans.jp" + re.sub("artists", "artist", url) + "?year=after")
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        results = [result.find("a").get("href") for result in soup.find_all("h3", attrs={"class": "artistName"})]
        dates = [result.text.split(" ")[0] for result in soup.find_all("p", attrs={"class": "date"})]
        results_mat = []
        for result, date in zip(results, dates):
            try:
                date = datetime.datetime.strptime(date, "%Y/%m/%d")
            except:
                continue
            if date > last_update:
                results_mat.append(result)                
                    
        results = results_mat
        
        if is_next_page:
            concerts += results
        else:
            concerts = results
        
        # continue with the next page
        next_page = soup.find('a', attrs={'rel': 'next'})
        if next_page:
            next_page_url = next_page.get('href')
            print(".", end="")
            return self.getConcerts(next_page_url, last_update=last_update, is_next_page=True, concerts=concerts)
            
        else:
            print()
            print("{}件のコンサートが見つかりました".format(len(concerts)))
            print()
            return concerts

    def getConcertInfo(self, url: str, artist: str) -> pd.DataFrame:
        print("artist: {}, event_url: {}".format(artist, url))
        print("OK. Let's start scraping concert info.")
        r = requests.get("https://www.livefans.jp" + url)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        
        try:
            # concert title
            title = soup.find("h4", attrs={"class": "liveName2"}).text
        except:
            print("Oops. You couldn't get concert title info. url: {}".format(url))
            title = None
            
        try:
            # concert location
            location = soup.find("address").text[1:]
        except:
            print("Oops. You couldn't get concert location info. url: {}".format(url))
            location = None
        
        try:
        # concert start time and end time
            date = soup.find("p", attrs={"class": "date"}).text.split(" ")[0]
            date = datetime.datetime.strptime(date, '%Y/%m/%d')
            print(date)
        except:
            date = None
            print("Oops. You couldn't get time info. url: {}".format(url))
        
        try:
            start_time = soup.find("p", attrs={"class": "date"}).text[:-3].split(")　")[-1]
            start_time = datetime.datetime.strptime(start_time, '%HH:%MM')
        except:
            start_time = None
            
        print("--------------")
        print()
        return pd.Series([title, artist, location, date, start_time, url], index=["title", "artist", "location", "date", "start_time", "url"])

        
    def getSetlist(self, concertUrl: str) -> list:
        print("getting setlist...")
        
        r = requests.get("https://www.livefans.jp" + concertUrl)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        setlist_block = soup.find("div", attrs={"class": ["setBlock", "nopscr"]})

        is_not_registered = len(setlist_block.find_all("p", attr={"class": "notice"}))
        if is_not_registered:
            return []
        
        setlist = setlist_block.find_all("tr")

        songs = [{"song": r.find("div", attrs={"class": "ttl"}).find("a").text, "url": r.find("div", attrs={"class": "ttl"}).find("a").get("href"), "lyric_url": r.find("a", attrs={"class": "utanet"}).get("href")} for r in setlist]
        print(songs)
        return songs

if __name__ == '__main__':
    artists = pd.read_excel("../firebase_artists.xlsx")
    lf = LiveFans()

    for index, artist in artists.iterrows():
        url = lf.searchArtist(artist["artistName"])

        if url == None:
            continue

        concert_urls = lf.getConcerts(url=url, last_update=artist["lastUpdate"], is_next_page=False, concerts=[])
        dates = []
        
        for concert_url in concert_urls:
            concert = lf.getConcertInfo(url=concert_url, artist=artist["name"])
            setlist = lf.getSetlist(concert_url)
            dates.append(concert["date"])
            
            title = concert["title"]    
            start_time = concert["start_time"]
                
            ustr= uuid.uuid4().hex
            
            concert_data = {
                "title": title,
                "artist": artist["artistName"],
                "goingUsers": [],
                "location": concert["location"],
                "date": concert["date"],
                "start_time": start_time,
                "setlist": setlist
            }
            print(concert_data)
            
            db.collection(u'concerts').document(ustr).set(concert_data)

            isRead = {} 
            for user in artist["favoriteUsers"]:
                isRead[user] = False
            
            if len(artist["favoriteUsers"]) != 0:
                notification_data = {
                    "type": "concert",
                    "artist": concert["artist"],
                    "notifId": ustr,
                    "isRead": isRead,
                    "users": artist["favoriteUsers"],
                    "createdAt": datetime.datetime.now()
                }

                db.collection(u'notifications').document().set(notification_data)
        
            if len(dates) == 0:
                continue

            lstupdate = { "lastUpdate": max(dates) }
            db.collection(u'artists').document(artist["id"]).update(lstupdate)
            print()
