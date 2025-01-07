from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import csv
import aiohttp
import asyncio

# Create an instance of the FastAPI application
# Connect the Jinja2 template to work with HTML templates (templates folder)
app = FastAPI()
templates = Jinja2Templates(directory='templates')

# Global Dictionary of Cities
cities = {}

# Function for loading a list of cities from a CSV file
# As a result, the cities will be saved to the global cities dictionary
def load_cities(filename):
    global cities
    with open(filename, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            city_name = row['capital']
            latitude = float(row['latitude'])
            longitude = float(row['longitude'])
            cities[city_name] = {'latitude': latitude, 'longitude': longitude, 'temperature': None}

# Load a list of cities
load_cities('europe.csv')

# Handler for the initial page index.html
# We explicitly indicate that this is HTML
@app.get('/', response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

# Handler for path GET /update
# It should return the cities and their temperatures to the Javascript in the index.html file
@app.get('/update')
async def fetch_weather():
    global cities

    # This nested function gets the temperature for a given city
    # using the open-meteo.com API
    async def fetch_city_weather(name, latitude, longitude):
        async with aiohttp.ClientSession() as session:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    temperature = data['current_weather']['temperature']
                    cities[name]['temperature'] = temperature
                else:
                    cities[name]['temperature'] = 'Error'

    # Create tasks for each city
    # and wait until they are all executed asynchronously
    tasks = [fetch_city_weather(city, details['latitude'], details['longitude']) for city, details in cities.items()]
    await asyncio.gather(*tasks)

    return cities