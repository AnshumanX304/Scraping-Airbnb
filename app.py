from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from flask import request, jsonify

app = Flask(__name__)

def connect_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_window_size(1280, 800)
    return driver

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
        
        return reviews
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
        reviews = scrape_airbnb_reviews(url)
        return jsonify({'reviews': reviews})
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