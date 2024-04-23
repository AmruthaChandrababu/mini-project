import requests
from bs4 import BeautifulSoup

def scrape_nitsurathkal():
    url = 'https://www.nitk.ac.in/upcoming_events'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find_all(class_="gdlr-core-event-item-content-wrap")
        event_list = []
        for event in events:
            event_text = event.get_text().strip()
            event_list.append(event_text)
        return event_list
    else:
        return []

events = scrape_nitsurathkal()
for event in events:
    print(event)
