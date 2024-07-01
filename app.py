from flask import Flask, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from flask import request, jsonify
import asyncio
import requests
import certifi
import io
import os
import gzip
import csv
from pymongo import MongoClient
from summariseReviews import summarize_reviews

app = Flask(__name__)

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI,tlsCAFile=certifi.where())
db = client['airbnb_data']
listings_collection = db['listings']

def connect_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_window_size(1280, 800)
    return driver

@app.route('/download_and_store_listings')
def download_and_store_listings():
    driver = connect_browser()
    try:
        driver.get("https://insideairbnb.com/get-the-data/")

        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "albany")))

        listings_link = table.find_element(By.XPATH, ".//a[contains(text(), 'listings.csv.gz')]")
        download_url = listings_link.get_attribute('href')

        response = requests.get(download_url)
        response.raise_for_status() 

        with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            listings = []
            for row in csv_reader:
                listings.append(row)
                if len(listings) == 1000:
                    listings_collection.insert_many(listings)
                    listings = []

            if listings:
                listings_collection.insert_many(listings)

        total_listings = listings_collection.count_documents({})

        return jsonify({
            'status': 'success',
            'message': f'Successfully stored {total_listings} listings in the database.',
            'total_listings': total_listings
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

    finally:
        driver.quit()

def scrape_airbnb_reviews(url):
    driver = connect_browser()
    
    try:
        driver.get(url)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="pdp-show-all-reviews-button"]')))
        
        show_all_reviews_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="pdp-show-all-reviews-button"]'))
        )
        show_all_reviews_button.click()
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="pdp-reviews-modal-scrollable-panel"]'))
        )
        
        review_elements = driver.find_elements(By.CSS_SELECTOR, '[data-review-id]')
        reviews = []
        
        for element in review_elements:
            name = element.find_element(By.CSS_SELECTOR, 'h2').text.strip()
            content = element.find_elements(By.CSS_SELECTOR, 'span')[-1].text.strip()
            reviews.append({'name': name, 'content': content})

        summarized_data=asyncio.run(summarize_reviews(reviews))
        # print(data)
        
        return {
            'reviews': reviews,
            'summary': summarized_data
        }
    except Exception as e:
        print('Error during scraping:', str(e))
        raise e
    finally:
        driver.quit()

def scrape_airbnb_amenities(url):
    driver = connect_browser()
    
    try:
        driver.get(url)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Show all') and contains(text(), 'amenities')]")))
        show_all_amenities_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show all') and contains(text(), 'amenities')]"))
        )
        show_all_amenities_button.click()

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="modal-container"]'))
        )
        
        amenities_elements = driver.find_elements(By.CSS_SELECTOR, "._11jhslp")
        amenities = []
        
        for element in amenities_elements:
            name = element.find_element(By.CSS_SELECTOR, 'h3').text.strip()
            content_amenities_element = element.find_elements(By.CSS_SELECTOR, 'li')
            services = []
            for item in content_amenities_element:
                service_text = item.find_element(By.XPATH, ".//div[contains(@class, 'twad414')]").text
                services.append(service_text)

            amenities.append({'name': name, "services": services})
        
        print("Button clicked!")
        return amenities
    except Exception as e:
        print('Error during scraping:', str(e))
        raise e
    finally:
        driver.quit()

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'URL parameter is missing'}), 400
    
    try:
        data = scrape_airbnb_reviews(url)
        return jsonify({'reviews': data['reviews'],
            "summarized_data": data['summary']})
    except Exception as e:
        print('Scraping error:', str(e))
        return jsonify({'error': 'An error occurred while scraping'}), 500
    
@app.route('/scrape-amenities')
def scrapeAmenities():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'URL parameter is missing'}), 400
    
    
    try:
        amenities = scrape_airbnb_amenities(url)
        return jsonify({'reviews': amenities})
    except Exception as e:
        print('Scraping error:', str(e))
        return jsonify({'error': 'An error occurred while scraping'}), 500

if __name__ == '__main__':
    app.run(port=3000)