import requests
from bs4 import BeautifulSoup

def scrape_nitnagpur():
    url = 'https://vnit.ac.in/category/events/'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find_all(class_="entry-article-part entry-article-header")
        event_list = []
        for event in events:
            results = event.find(class_="entry-title entry--item")
            event_text = results.get_text()
            cleaned_event = ' '.join(event_text.split())
            event_list.append(cleaned_event)
        return event_list
    else:
        return []

events = scrape_nitnagpur()
for event in events:
    print(event)
