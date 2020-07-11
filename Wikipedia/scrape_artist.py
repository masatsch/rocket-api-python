import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import os
import json
import uuid
import datetime

class Wikipedia:
    def get_homepage_url(self, artist: str) -> str:
        print("Let's get homepage url!!")
        try:
            r = requests.get("https://ja.wikipedia.org/wiki/" + artist)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'html.parser')
            homepage_url = soup.find("table", attrs={"class": ["infobox", "vcard", "plainlist"]}).find("a", attrs={"rel": "nofollow", "class": ["external", "text"]}).get("href")
            return homepage_url
        except:
            print("you couldn't find homepage url: {}".format(artist))
            return None
        
    def get_member(self, artist: str) -> dict:
        print("Let's get member list!!")
        try:
            r = requests.get("https://ja.wikipedia.org/wiki/" + artist)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'html.parser')
            result = soup.find("table", attrs={"class": ["infobox", "vcard", "plainlist"]}).find_all("tr")[-3].find("td").text[1:]

            raw_list = re.split("[（）]", result)
            count = 0
            member = []
            for raw in raw_list:
                if raw == '' or '年' in raw:
                    continue

                count += 1
                if count % 2 ==0:
                    continue

                member.append(raw)

            return member
        except:
            print("you couldn't find member info: {}".format(artist))
            return None
        
    def getTag(self, artist: str, tag: str) -> str:
        try:
            r = requests.get("https://ja.wikipedia.org/wiki/" + artist)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'html.parser')
            result = soup.find("table", attrs={"class": ["infobox", "vcard", "plainlist"]})
            tr_list = result.find_all("tr")
            for tr_tag in tr_list:
                th_tag = tr_tag.find("th")
                if th_tag.text == tag:
                    print("Gotcha!")
                    return tr_tag.find("td").text
                
            return None
        except:
            print("section does not exist")
            return None


if __name__ == '__main__':
    wiki = Wikipedia()
    homepages = []
    members = []
    offices = []
    labels = []
    for artist in artistName:
        homepage_url = wiki.get_homepage_url(artist)
        member = wiki.get_member(artist)
        office = wiki.getTag(artist, "事務所")
        label = wiki.getTag(artist, "レーベル")
        offices.append(office)
        labels.append(label)
        homepages.append(homepage_url)
        members.append(member)

    artists = pd.DataFrame({"artistName": artistName, "members": members, "homepages": homepages, "office": offices, "label": labels})
    artists.to_excel("../scraped_artists.xlsx")