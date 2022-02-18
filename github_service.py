#!/usr/bin/env python
import socket
import requests
import time
import json
import const
from datetime import datetime, timedelta
import threading

BASE_URL = 'https://api.github.com/search/{}?q={}&per_page=100'
INTERVAL_URL = 'https://api.github.com/search/{}?q={} created:{}..{}&per_page=100'

# Sleep time (wait for GitHub to accept requests)
SLEEP_TIME = 2 # second
RATE_LIMIT = 60 # second

DATE_FORMAT = '%Y-%m-%d'

# Default interval
INTERVAL = 3 # days

class GitHubService:
    def __init__(self) -> None:
        self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mySocket.bind(("localhost", 1205))
        self.mySocket.listen(1)
        self.conn, _ = self.mySocket.accept()

    def getRepoLangByKeywordSmallInterval(self, keyword, startDate, endDate):
        url = INTERVAL_URL.format('repositories', keyword, startDate, endDate)
        while (True):
            langs = keyword + "$$$"
            response = requests.get(url)

            if not response.ok:
                time.sleep(SLEEP_TIME)
                response = requests.get(url)

            try:
                items = json.loads(response.text)['items']
            except KeyError:
                time.sleep(RATE_LIMIT)
                response = requests.get(url)
                items = json.loads(response.text)['items']

            for item in items:
                if item['language'] is None:
                    continue
                langs += item['language'] + "\t"

            langs = langs[:-1] + '\n'
            self.conn.send(bytes(langs, 'utf-8'))
            url = response.links.get('next', None)
            if url is None:
                break
            url = url['url']
        return langs

    def getAllRepoLangByKeyword(self, keyword, startDate, endDate, interval = INTERVAL):
        result = ""

        startIntervalDate = datetime.strptime(startDate, DATE_FORMAT)
        endIntervalDate = startDate

        lastDate = datetime.strptime(endDate, DATE_FORMAT)

        while endIntervalDate != lastDate:
            endIntervalDate = min(startIntervalDate + timedelta(days=interval), lastDate)
            result += self.getRepoLangByKeywordSmallInterval(
                            keyword,
                            startIntervalDate.strftime(DATE_FORMAT),
                            endIntervalDate.strftime(DATE_FORMAT))
            startIntervalDate = endIntervalDate + timedelta(days=1)

        return result
    
    def getAllRepoLangByKeywordsList(self, startDate, endDate, keywords = const.KEYWORDS, interval = INTERVAL):
        for keyword in keywords:
            thread = threading.Thread(target=self.getAllRepoLangByKeyword, args=[keyword, startDate, endDate, interval])
            thread.start()
        
service = GitHubService()
end = datetime.now()
start = end - timedelta(days=180)
service.getAllRepoLangByKeywordsList(start.strftime(DATE_FORMAT), end.strftime(DATE_FORMAT))