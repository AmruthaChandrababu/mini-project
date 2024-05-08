import requests
from bs4 import BeautifulSoup

def scrape_nitjaipur():
    url = 'https://mnit.ac.in/news/newsall?type=event'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        event_list = []
        event_divs = data.find_all(id="pills-2")
        for div in event_divs:
            event_tags = div.find_all('a')
            for event in event_tags:
                event_text = event.get_text().strip()
                event_list.append(event_text)
        return event_list
    else:
        return []

events = scrape_nitjaipur()
for event in events:
    print(event)
