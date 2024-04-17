import requests
from bs4 import BeautifulSoup

def scrape_nit():
    url = 'https://www.nitt.edu/home/academics/departments/meta/events/workshops/'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events_container = data.find("div", id="contentcontainer")
        if events_container:
            event_elements = events_container.find_all("li")
            event_text = [event.get_text(strip=True) for event in event_elements]
            return event_text
        else:
            return "No events found on the page"
    else:
        return "Failed to retrieve the webpage"

# Test the function
events = scrape_nit()
for event in events:
    print("Event name:", event)
