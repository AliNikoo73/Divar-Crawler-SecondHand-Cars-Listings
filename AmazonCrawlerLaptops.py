from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
# from pyvirtualdisplay import Display
from selenium import webdriver
# import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
import time
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection string
db = client['amazon_db']  # Database name
collection = db['listings_laptops']  # Collection name

options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--enable-javascript')
options.add_argument('--disable-dev-shm-usage')
service = Service(
    executable_path=r"D:\\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
# URL of the website you want to crawl
url = 'https://www.amazon.ca/'

# Open the website
driver.get(url)
ads = []
urls = []
scrolls = 1
try:
    driver.find_elements(By.CLASS_NAME, "nav-a")[12].click()
    time.sleep(3)
    driver.find_elements(By.CLASS_NAME, "bxc-grid-overlay__link")[1].click()
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    driver.find_elements(By.ID, "apb-desktop-browse-search-see-all")[0].click()
    time.sleep(1)
    for _ in range(int(driver.find_elements(By.CLASS_NAME, "s-pagination-item")[5].get_attribute("textContent")) // 50):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        for _ in range(scrolls):
            # Find elements and append them as a list to ELEMENTS
            elements_on_scroll = driver.find_elements(By.CLASS_NAME,"a-link-normal")[::2]
            ads.append(elements_on_scroll)
            for element in elements_on_scroll:
                href = element.get_attribute('href')
                if href and href not in urls:  # Avoid duplicates
                    urls.append(href)
        time.sleep(1)
        next_page = driver.find_elements(By.CLASS_NAME, "s-pagination-item")[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
        time.sleep(1)  # Allow time for any scrolling or animations
        next_page.click()

    print("----------------------------------------------------------------")
    print(len(urls))
    print("----------------------------------------------------------------")

    for url in urls:
        driver.get(url)
        time.sleep(5)
        # Extracting data
        try:
            # Extract title
            title_element = driver.find_elements(By.CLASS_NAME, "a-size-large")[5]
            title = title_element.text if title_element else "N/A"
            print(f"Title : {title}")
            print("----------------------------------------------------------------")

            # Extract price
            price_elements = [driver.find_elements(By.CLASS_NAME, "a-price-symbol")[0],
                              driver.find_elements(By.CLASS_NAME, "a-price-whole")[0],
                              driver.find_elements(By.CLASS_NAME, "a-price-fraction")[0]]
            price = str(price_elements[0].text + price_elements[1].text + "." + price_elements[2].text)
            print(f"Price : {price}")
            print("----------------------------------------------------------------")

            # Extract descriptions
            # Find the unordered list by its tag or another identifying attribute
            description_element = driver.find_elements(By.CLASS_NAME, "a-spacing-mini")
            # print(description_element)

            # Initialize a list to store the text content of each <li>
            list_items_text = []
            # Find all the list items <li> within the <ul> element
            for d in description_element:
                if d.tag_name == "li":
                    li_elements = d.get_attribute("textContent")
                    list_items_text.append(li_elements.strip())
            # print(list_items_text)
            description = "\n".join(list_items_text)
            print(f"Description : {description}")
            print("----------------------------------------------------------------")

            # Extract other features (add more as needed)
            features = {}
            feature_elements = [title, price, description]
            feature_labels = ["Title", "Price", "Description"]

            # feature_elements_extra = driver.find_elements(By.CLASS_NAME, "kt-base-row__title")[1:-1]

            # # Loop through all the "kt-base-row__title" elements
            # for idx, feature_element in enumerate(feature_elements_extra):
            #     feature_name = feature_element.text.strip()
            #     # Assuming each feature label has a corresponding value element
            #     value_elements = driver.find_elements(By.CLASS_NAME, "kt-unexpandable-row__value")
            #     if idx < len(value_elements):
            #         feature_value = value_elements[idx].text.strip()
            #         features[feature_name] = feature_value

            # Prepare document to store in MongoDB
            document = {
                "url": url,
                "Title": title,
                "description": description,
                "price": price,
                "timestamp": time.time()  # Optional: Store a timestamp of extraction
            }

            # Insert into MongoDB
            collection.insert_one(document)

            print(f"Data for URL {url} inserted successfully.")
            print("----------------------------------------------------------------")

        except Exception as e:
            print(f"Error extracting data for {url}: {e}")

except TimeoutException:
    print("Timeout while waiting for page or elements to load.")

# Quit the browser once done
driver.quit()

# Testing the robot
# while True:
#     pass
