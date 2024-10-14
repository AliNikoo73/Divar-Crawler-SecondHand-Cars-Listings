import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection string
db = client['divar_db']  # Database name


# URL of the website you want to crawl
url = 'https://divar.ir'

# Open the website
driver = webdriver.Chrome()  # Ensure you have the correct webdriver for your browser
driver.get(url)

all_section_urls = {}  # Store URLs categorized by sections

# Wait for the page to load and for specific elements to appear
try:
    driver.find_elements(By.CLASS_NAME, 'city-card-fffcd')[4].click()
    time.sleep(2)
    driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[1].click()
    time.sleep(2)
    driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[2].click()
    time.sleep(2)
    # Get all the 'kt-accordion-item__header' elements you want to iterate through
    accordion_headers = driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[3:7]
    
    # Loop through each accordion header and collect URLs
    for index, header in enumerate(accordion_headers):
        section_name = f'section_{index + 1}'
        all_section_urls[section_name] = []  # Initialize URL list for the current section
        
        # Click to expand the section
        header.click()
        time.sleep(2)  # Give time for the page to load

        scrolls = 1
        # Scroll the page and collect WebElements
        for _ in range(scrolls):
            # Find elements and append them to the current section list
            elements_on_scroll = driver.find_elements(By.CLASS_NAME, "kt-post-card__action")
            for element in elements_on_scroll:
                href = element.get_attribute('href')
                if href and href not in all_section_urls[section_name]:  # Avoid duplicates
                    all_section_urls[section_name].append(href)

            # Scroll down the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Navigate back to the main page for the next section
        driver.get(url)
        time.sleep(2)
        driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[1].click()
        time.sleep(2)
        driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[2].click()
        time.sleep(2)

        # Re-locate the accordion headers since the page reloads
        accordion_headers = driver.find_elements(By.CLASS_NAME, 'kt-accordion-item__header')[3:7]

    # Save all collected URLs to a CSV file
    with open('section_urls.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Section', 'URL'])  # Write header
        
        for section_name, urls in all_section_urls.items():
            for url in urls:
                writer.writerow([section_name, url])

    print("URLs saved to section_urls.csv")
    
    # Iterate over each section's URLs and extract data to a separate collection
    for section_name, urls in all_section_urls.items():
        collection_name = f'divar_{section_name}'  # Creating a collection name based on section
        collection = db[collection_name]  # Replace `db` with your MongoDB database instance

        for url in urls:
            driver.get(url)
            time.sleep(5)
            
            # Extracting data
            try:
                # Extract model
                model_element = driver.find_elements(By.CLASS_NAME, "kt-unexpandable-row__action")[0]
                model = model_element.text if model_element else "N/A"

                # Extract price
                price_element = driver.find_elements(By.CLASS_NAME, "kt-unexpandable-row__value")[-1]
                price = price_element.text if price_element else "N/A"

                # Extract mileage
                mileage_element = driver.find_elements(By.CLASS_NAME, "kt-group-row-item")[3]
                mileage = mileage_element.text if mileage_element else "N/A"

                # Extract year
                year_element = driver.find_elements(By.CLASS_NAME, "kt-group-row-item")[4]
                year = year_element.text if year_element else "N/A"

                # Extract color
                color_element = driver.find_elements(By.CLASS_NAME, "kt-group-row-item")[5]
                color = color_element.text if color_element else "N/A"

                # Extract other features (add more as needed)
                features = {}
                feature_elements_extra = driver.find_elements(By.CLASS_NAME, "kt-base-row__title")[1:-1]

                # Loop through all the "kt-base-row__title" elements
                for idx, feature_element in enumerate(feature_elements_extra):
                    feature_name = feature_element.text.strip()
                    # Assuming each feature label has a corresponding value element
                    value_elements = driver.find_elements(By.CLASS_NAME, "kt-unexpandable-row__value")
                    if idx < len(value_elements):
                        feature_value = value_elements[idx].text.strip()
                        features[feature_name] = feature_value

                # Prepare document to store in MongoDB
                document = {
                    "url": url,
                    "model-make": model,
                    "price": price,
                    "mileage": mileage,
                    "year": year,
                    "color": color,
                    "additional_features": features,  # Store all optional features here
                    "timestamp": time.time()  # Optional: Store a timestamp of extraction
                }

                # Insert into the appropriate MongoDB collection
                collection.insert_one(document)

                print(f"Data for URL {url} inserted successfully into collection {collection_name}.")
                print("----------------------------------------------------------------")

            except Exception as e:
                print(f"Error extracting data for {url}: {e}")

except TimeoutException:
    print("Timeout while waiting for page or elements to load.")

# Quit the browser once done
driver.quit()
