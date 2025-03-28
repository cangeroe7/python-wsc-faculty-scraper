import boto3
import requests
import pandas as pd
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from io import BytesIO
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Department Enum List
VALID_DEPARTMENTS = [
    "Art and Design",
    "Business and Economics",
    "Communication Arts",
    "Computer Technology and Information Systems",
    "Counseling",
    "Criminal Justice",
    "Educational Foundations and Leadership",
    "Health, Human Performance, and Sport",
    "History, Politics, and Geography",
    "Language and Literature",
    "Life Sciences",
    "Music",
    "Physical Sciences and Mathematics",
    "Psychology and Sociology",
    "Technology and Applied Science",
]

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    region_name="us-east-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
BUCKET_NAME = os.getenv("BUCKET_NAME")

# PostgreSQL Configuration
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Selenium Configuration
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(
    service=Service("/usr/bin/chromedriver"), options=chrome_options
)

def clean_value(value, max_length=None):
    """
    Clean input value:
    - Convert 'N/A' to None
    - Truncate to max_length if specified
    - Convert to string if not None
    """
    if pd.isna(value) or str(value).strip().upper() == 'N/A':
        return None
    
    cleaned = str(value).strip()
    return cleaned[:max_length] if max_length and len(cleaned) > max_length else cleaned

def validate_department(department):
    """
    Validate and standardize department name
    """
    if not department or str(department).strip().upper() == 'N/A':
        return None
    
    # Try to find an exact match (case-insensitive)
    cleaned_dept = str(department).strip()
    for valid_dept in VALID_DEPARTMENTS:
        if cleaned_dept.lower() == valid_dept.lower():
            return valid_dept
    
    # If no exact match, print a warning
    print(f"Warning: Department '{department}' does not match any predefined department. Skipping.")
    return None

def fetch_image(image_url):
    try:
        driver.get(image_url)
        img_element = driver.find_element("tag name", "img")
        img_src = img_element.get_attribute("src")
        response = requests.get(img_src)
        if response.status_code != 200:
            return None
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error fetching image {image_url}: {e}")
        return None

def upload_to_s3(image_url, name):
    # Skip S3 upload for None or 'N/A'
    if not image_url or str(image_url).strip().upper() == 'N/A':
        return None
    
    if not str(image_url).startswith("http"):
        return None
    
    image_buffer = fetch_image(image_url)
    if not image_buffer:
        return None
    
    file_name = f"images/{name.replace(' ', '_')}.jpg"
    s3.upload_fileobj(
        image_buffer, BUCKET_NAME, file_name, ExtraArgs={"ContentType": "image/jpeg"}
    )
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_name}"

def process_csv(file_path, start_at=0, default_timeslots_per_hour=2):
    df = pd.read_csv(file_path)
    
    for index, row in df.iterrows():
        # Check if the current index is less than the start_at value
        if index < start_at:
            continue  # Skip rows until start point
        
        try:
            print(f"Processing index {index}: {row['Name']}")
            
            # Validate required fields
            name = clean_value(row["Name"])
            if not name:
                print(f"Skipping row {index} - Name is required")
                continue
            
            # Handle image URL upload
            new_image_url = upload_to_s3(row["Image URL"], name)
            
            # Clean and prepare values
            title = clean_value(row.get("Title"), 50)
            position = clean_value(row["Position"], 50)
            if not position:
                print(f"Skipping row {index} - Position is required")
                continue
            
            # Validate department
            department = validate_department(row.get("Department"))
            if not department:
                print(f"Skipping row {index} - Invalid or missing department")
                continue
            
            office_location = clean_value(row.get("Office Location"), 50)
            phone = clean_value(row.get("Phone"), 20)
            email = clean_value(row["Email"])
            
            if not email:
                print(f"Skipping row {index} - Email is required")
                continue
            
            # Insert into database
            cursor.execute(
                """
                INSERT INTO staff (
                    name, title, photo_url, position, 
                    department, office_location, phone, email, timeslots_per_hour
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name, title, new_image_url, position, 
                    department, office_location, phone, email, 
                    default_timeslots_per_hour
                ),
            )
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            print(f"Skipping {row['Name']} - email already exists")
            conn.rollback()
        except Exception as e:
            print(f"Error at index {index} for {row['Name']}: {e}")
            conn.rollback()
    
    driver.quit()
    cursor.close()
    conn.close()

# Start from a specific line if passed as an argument
start_line = int(sys.argv[1]) if len(sys.argv) > 1 else 0
process_csv("filtered_output.csv", start_line)
