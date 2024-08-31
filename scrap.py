from py3pin.Pinterest import Pinterest
import csv
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve Pinterest credentials from environment variables
email = os.getenv('PINTEREST_EMAIL')
password = os.getenv('PINTEREST_PASSWORD')
username = os.getenv('PINTEREST_USERNAME')

def scrape_pinterest(keywords):
    pinterest = Pinterest(email=email,
                          password=password,
                          username=username)

    pinterest.login()

    results = []

    for keyword in keywords:
        print(f"Scraping data for keyword: {keyword}")
        search_results = pinterest.search(scope='pins', query=keyword, page_size=100)

        for pin in search_results:
            pin_data = {
                "Image URL": pin.get("images", {}).get("orig", {}).get("url"),
                "Description": pin.get("description"),
                "Pin URL": pin.get("link"),
                "Title": pin.get("title"),
                "ID": pin.get("id")
            }
            results.append(pin_data)

    return results

def save_to_csv(data, filename='pinterest_scrape_results.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["ID", "Title", "Image URL", "Description", "Pin URL"])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    keywords = ["Kitchen DIY Ideas "]
    scraped_data = scrape_pinterest(keywords)
    save_to_csv(scraped_data)
