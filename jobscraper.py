import requests
import json
from bs4 import BeautifulSoup
import time as tm
from urllib.parse import quote

def load_config(file_name):
    # Load the config file
    with open(file_name) as f:
        return json.load(f)

def get_with_retry(url, config, retries=3, delay=1):
    # Get the URL with retries and delay
    for i in range(retries):
        try:
            if len(config['proxies']) > 0:
                r = requests.get(url, headers=config['headers'], proxies=config['proxies'], timeout=5)
            else:
                r = requests.get(url, headers=config['headers'], timeout=5)
            return BeautifulSoup(r.content, 'html.parser')
        except requests.exceptions.Timeout:
            print(f"Timeout occurred for URL: {url}, retrying in {delay}s...")
            tm.sleep(delay)
        except Exception as e:
            print(f"An error occurred while retrieving the URL: {url}, error: {e}")
    return None

def transform(soup):
    # Parse the job card info (title, company, location, date, job_url) from the BeautifulSoup object
    joblist = []
    try:
        divs = soup.find_all('div', class_='base-search-card__info')
    except:
        print("Empty page, no jobs found")
        return joblist

    for item in divs:
        title = item.find('h3').text.strip()
        company = item.find('a', class_='hidden-nested-link')
        location = item.find('span', class_='job-search-card__location')
        parent_div = item.parent
        entity_urn = parent_div['data-entity-urn']
        job_posting_id = entity_urn.split(':')[-1]
        job_url = f'https://www.linkedin.com/jobs/view/{job_posting_id}/'

        date_tag_new = item.find('time', class_='job-search-card__listdate--new')
        date_tag = item.find('time', class_='job-search-card__listdate')
        date = date_tag['datetime'] if date_tag else date_tag_new['datetime'] if date_tag_new else ''
        job = {
            'title': title,
            'company': company.text.strip() if company else '',
            'location': location.text.strip() if location else '',
            'date': date,
            'job_url': job_url,
        }
        joblist.append(job)
    return joblist

def get_jobcards(config):
    # Function to get the job cards from the search results page
    all_jobs = []
    for query in config['search_queries']:
        keywords = quote(query['keywords'])  # URL encode the keywords
        location = quote(query['location'])  # URL encode the location
        for i in range(config['pages_to_scrape']):
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_TPR=&f_WT={query['f_WT']}&geoId=&f_TPR={config['timespan']}&start={25 * i}"
            soup = get_with_retry(url, config)
            jobs = transform(soup)
            all_jobs.extend(jobs)
            print(f"Finished scraping page: {url}")
    return all_jobs

def main(config_file):
    start_time = tm.perf_counter()
    config = load_config(config_file)

    # Scrape job cards from LinkedIn
    all_jobs = get_jobcards(config)
    print(f"Total jobs scraped: {len(all_jobs)}")

    # Display the scraped jobs
    for job in all_jobs:
        print(f"Title: {job['title']}, Company: {job['company']}, Location: {job['location']}, Date: {job['date']}, URL: {job['job_url']}")

    end_time = tm.perf_counter()
    print(f"Scraping finished in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    config_file = 'config.json'  # default config file
    main(config_file)
