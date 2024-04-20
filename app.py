from flask import Flask, render_template,url_for,request,session
from bson import ObjectId 
#from pymongo import mongo
from flask import redirect
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import schedule
import time
import bcrypt

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

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
def scrape_cet():
    url = 'https://www.cet.ac.in/short-term-courses/'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find(id="lcp_instance_0")
        event_text = events.get_text(separator='\n')
        return event_text.strip()
    else:
        return []

def scrape_nit():
    url = 'https://nitc.ac.in/upcoming-events'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find(class_="xc-page-column-right")
        results = events.find(class_="xc-calendar-list")
        event_text = results.get_text(separator='\n')
        return event_text.strip()
    else:
        return []

#def scrape_iitb():
    url = 'https://www.iitb.ac.in/events'
    response = requests.get(url)
    if response.status_code == 200:
        text = response.content
        data = BeautifulSoup(text, 'html.parser')
        events = data.find(class_="fc-list-table")
        results = events.find(class_="fc-list-item fc-has-url")
        event_text = results.get_text(separator='\n')
        return event_text.strip()
    else:
        return []

# Function to scrape events from all college websites and update MongoDB
def scrape_and_update():
    #collection.delete_many({})
    events_cet = scrape_cet()
    events_nit = scrape_nit()
    #events_iitb = scrape_iitb()
    print("CET events:", events_cet)
    print("NIT events:", events_nit)
    #print("IITB events:", events_iitb)
    collection.insert_one({'college': 'Cet', 'events': events_cet.split('\n')})
    collection.insert_one({'college': 'nit', 'events': events_nit.split('\n')})
    #collection.insert_one({'college': 'iitb', 'events': events_iitb.split('\n')})
    print("Events scraped and updated in MongoDB")

# Schedule the scraping and updating task to run every 60 seconds
schedule.every(60).seconds.do(scrape_and_update)

# Flask route to render the index.html template with scraped data
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event-details')
def event_details():
    # Fetch data from MongoDB and convert cursor to list of dictionaries
    cursor = collection.find({}, {'_id': 0})
    scraped_data = [doc for doc in cursor]
    
    # Create a dictionary with 'college' as keys and 'events' as values
    scraped_data_dict = {doc['college']: doc['events'] for doc in scraped_data}

    return render_template('event-details.html', scraped_data=scraped_data_dict)


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
    
    if request.method == 'POST':
        college = request.form['college']  # Retrieve the college name from the form
        event_name = request.form['event_name']  # Retrieve the event name from the form
        
        # Check if both college and event_name fields are provided
        if not college or not event_name:
            return "Error: College and event name are required fields"

        # Find the document corresponding to the provided college name
        # Assuming you have a MongoDB collection named 'events'
        event_doc = collection.find_one({'college': college})
        if event_doc:
            # Update the events list with the new event name
            collection.update_one({'_id': event_doc['_id']}, {'$push': {'events': event_name}})
        else:
            # If the college does not exist, create a new document
            collection.insert_one({'college': college, 'events': [event_name]})
        
        return redirect(url_for('dashboard'))
    else:
        return "Error: Method not allowed"


# Delete event route (for admins only) 

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Retrieve the event ID from the form data
        event_id = request.form.get('event_id')

        # Convert the event ID to ObjectId
        event_id = ObjectId(event_id)

        # Delete the event from the MongoDB collection
        collection.delete_one({'_id': event_id})
        
        return redirect(url_for('dashboard'))

    # If accessed via GET request, redirect back to the dashboard
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
