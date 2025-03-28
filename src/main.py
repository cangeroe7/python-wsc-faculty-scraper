import time
import csv
import string
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up Selenium with headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Initialize Selenium WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Base URL pattern
base_url = "https://www.wsc.edu/directory/9/a-to-z/{}?page={}"

# Function to scrape a single page
def scrape_page():
    time.sleep(2)  # Ensure page is loaded
    soup = BeautifulSoup(driver.page_source, "html.parser")

    people = []
    
    for person in soup.select(".wsc-facstaff-person-list-container"):
        # Extract full name
        name_tag = person.select_one(".wsc-facstaff-person-list-namejob strong a")
        full_name = name_tag.text.strip() if name_tag else "N/A"

        # Split name and title
        name_parts = full_name.split(", ")
        name = name_parts[0]
        title = name_parts[1] if len(name_parts) > 1 else "N/A"

        # Extract position
      # Extract position safely
        position_tag = person.select_one(".wsc-facstaff-person-list-namejob p")
        if position_tag:
            position_text = list(position_tag.stripped_strings)
            position = position_text[-1] if len(position_text) > 1 else "N/A"
        else:
            position = "N/A"

        # Extract image URL
        img_tag = person.select_one(".wsc-facstaff-person-list-photo img")
        image_url = "https://www.wsc.edu" + img_tag["src"] if img_tag else "N/A"

        # Extract department
        department_tag = person.select_one(".wsc-facstaff-person-list-2.box1")
        department = department_tag.text.replace("Department:", "").strip() if department_tag else "N/A"

        # Extract office location
        office_tag = person.select_one(".wsc-facstaff-person-list-2.box2")
        office_location = office_tag.text.replace("Office location:", "").strip() if office_tag else "N/A"

        # Extract phone number
        phone_tag = person.select_one(".wsc-facstaff-person-list-3 .box1 a")
        phone = phone_tag.text.strip() if phone_tag else "N/A"

        # Extract email
        email_tag = person.select_one(".wsc-facstaff-person-list-3 .box2 a")
        email = email_tag["href"].replace("mailto:", "").strip() if email_tag else "N/A"

        people.append([name, title, position, image_url, department, office_location, phone, email])

    return people

# Scrape all pages until no more faculty members are found
all_people = []
for letter in string.ascii_uppercase:

    page_num = 1

    while True:
        url = base_url.format(letter, page_num)
        print(f"Scraping page {page_num} for letter {letter}...")
        driver.get(url)

        try:
            # Wait for faculty container to appear (if it doesn't, we've reached the last page)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wsc-facstaff-person-list-container"))
            )
        except:
            print(f"Reached end of directory for {letter}. Stopping.")
            break

        all_people.extend(scrape_page())
        page_num += 1

# Close WebDriver
driver.quit()

# Save to CSV
csv_filename = "faculty_directory.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Title", "Image URL", "Department", "Office Location", "Phone", "Email"])
    writer.writerows(all_people)

print(f"Scraping complete! Data saved to {csv_filename}")
