import requests
from bs4 import BeautifulSoup

def scrape_iitbhu():
    url = 'https://www.iitbhu.ac.in/events'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find_all(class_="text-align-justify")
        event_list = []
        for event in events:
            event_text = event.get_text().strip()
            event_list.append(event_text)
        return event_list
    else:
        return []

events = scrape_iitbhu()
for event in events:
    print(event)
