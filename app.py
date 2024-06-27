from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

@app.route('/scrape')
def scrape():
    url = "https://www.airbnb.co.in/rooms/858697692672545141?category_tag=Tag%3A8678&enable_m3_private_room=true&photo_id=1728488302&search_mode=regular_search&check_in=2024-06-28&check_out=2024-06-29&source_impression_id=p3_1719410416_P3fACuyveajy0eSk&previous_page_section_name=1000&federated_search_id=49a88c11-aa1c-43f2-9125-e1e8745a3d3b&locale=en&_set_bev_on_new_domain=1719467012_EAMjIxZjFiMTg3NT"
    
    try:
        reviews = scrape_airbnb_reviews(url)
        return jsonify({'reviews': reviews})
    except Exception as e:
        print('Scraping error:', str(e))
        return jsonify({'error': 'An error occurred while scraping'}), 500

if __name__ == '__main__':
    app.run(port=3000)