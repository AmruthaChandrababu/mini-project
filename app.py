from flask import Flask, render_template,request,session,schedule,url_for
from flask import redirect
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import bcrypt

app = Flask(__name__)

# MongoDB configuration
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'college_events_db'
COLLECTION_NAME = 'events'
ADMIN_COLLECTION_NAME = 'admin'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
admin_collection = db[ADMIN_COLLECTION_NAME]


# Function to scrape events from College A website
url = 'https://www.iitpkd.ac.in/past-events'

# Define the keywords to search for
keywords = ['workshop', 'lecture', 'convention', 'research']

# Function to extract text content from past events section of the webpage
def extract_text_after_past_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all text siblings of elements containing "Past events"
    past_events_header = soup.find(string='Past events')

    if past_events_header:
        # Initialize a flag to indicate when to start capturing text
        capture_text = False
        text_sections = []

        # Loop through the siblings of the past events header
        for sibling in past_events_header.find_all_next(string=True):
            # Check if the sibling is a tag
            if sibling.name:
                # Check if the sibling is pagination section
                if sibling.get('id') == 'table-pagination':
                    break  # Stop capturing text if pagination section is encountered
            else:
                # Capture the text if not pagination section
                for keyword in keywords:
                    if keyword in sibling.lower():
                        text_sections.append(sibling.strip())
                        break  # Once a keyword is found, move to the next sibling

        return text_sections
    else:
        return []

# Main function to scrape data
def scrape_data(url):
    text = extract_text_after_past_events(url)
    return text


def scrape_nit():
    url='https://nitc.ac.in/upcoming-events'
    response = requests.get(url)
    if response.status_code == 200:
        text=response.content
        data=BeautifulSoup(text,'html.parser')
        events=data.find(class_="xc-page-column-right")
        results=events.find(class_="xc-calendar-list")
        event_text = results.get_text(separator='\n')
        return event_text.strip()
    else:
        return []
    
def scrape_nitTrichy():
    url = 'https://www.nitt.edu/home/academics/departments/meta/events/workshops/'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events_container = data.find("div", id="contentcontainer")
        if events_container:
            event_elements = events_container.find_all("li")
            event_text = [event.get_text(strip=True) for event in event_elements]
            for i in range(len(event_text)):
                event_text[i] = ' '.join(event_text[i].split())
            return event_text
        else:
            return "No events found on the page"
    else:
        return "Failed to retrieve the webpage"
    
def scrape_cet():
    url='https://www.cet.ac.in/short-term-courses/'
    response = requests.get(url)
    if response.status_code == 200:
        text=response.content
        data=BeautifulSoup(text,'html.parser')
        events=data.find(id="lcp_instance_0")
        event_text = events.get_text(separator='\n')
        return event_text.strip()
    else:
        return []


   
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event-details')
def event_details():
    collection.delete_many({})
    # Scrape events from College A and College B
    events_iit = scrape_data(url)
    events_nitTrichy = scrape_nitTrichy()
    events_nit = scrape_nit()
    events_cet = scrape_cet()
    
    print("IIT events:", events_iit)
    print("NIT Trichy events:", events_nitTrichy)
    print("NIT events:", events_nit)
    print("CET events:", events_cet)
    # Store the scraped events in MongoDB
    college_data = [
        {'college': 'IIT Palakkad', 'url': 'https://www.iitpkd.ac.in/past-events', 'events': events_iit},
        {'college': 'NIT Trichy', 'url': 'https://www.nitt.edu/home/academics/departments/meta/events/workshops/', 'events': events_nitTrichy},
        {'college': 'NIT Calicut', 'url': 'https://nitc.ac.in/upcoming-events', 'events': events_nit.split('\n')},
        {'college': 'CET', 'url': 'https://www.cet.ac.in/short-term-courses/', 'events': events_cet.split('\n')}
    ]
    
    collection.insert_one({'colleges': college_data})
    
    # Retrieve the scraped events from MongoDB
    scraped_data = collection.find_one({}, {'_id': 0})

    print("Scraped data:", scraped_data)  # Print scraped data for debugging
    

    return render_template('event-details.html', scraped_data=scraped_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

#@app.route('/login')
#def login():
    return render_template('login.html')

@app.route('/ticket-details')
def ticket_details():
    return render_template('ticket-details.html')

# Admin login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = admin_collection.find_one({'username': username})

        if admin:
            if bcrypt.checkpw(password.encode('utf-8'), admin['password']):
                session['admin_id'] = str(admin['_id'])
                return redirect(url_for('dashboard'))

        # Login failed
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

# Admin logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin dashboard route
@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    events = collection.find()
    return render_template('dashboard.html', events=events)

# Add event route (for admins only)
@app.route('/add_event', methods=['POST'])
def add_event():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Add event logic here
    return redirect(url_for('dashboard'))

# Delete event route (for admins only)
@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Delete event logic here
    return redirect(url_for('dashboard'))

# Register admin route (optional)
@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if admin_collection.find_one({'username': username}):
            return render_template('register_admin.html', error='Username already exists')

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert admin into database
        admin_collection.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('login'))

    return render_template('register_admin.html')

if __name__ == '__main__':
    app.run(debug=True)
