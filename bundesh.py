import pandas as pd
import re
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    options.add_argument('--lang=en-US')
    options.add_argument('--window-size=1200,1000')
    user_data_dir = r'C:\Users\Boy Cakaraningrat\AppData\Local\Google\Chrome\User Data'
    profile_directory = 'Profile 2'
    options.add_argument(f'--user-data-dir={user_data_dir}')
    options.add_argument(f'--profile-directory={profile_directory}')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0.0.0 Safari/537.36")
    service = Service(r'C:/Users/Boy Cakaraningrat/New folder/New folder/chromedriver-win64/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scroll_page(driver, scroll_pause_time=2):
    """
    Scrolls the webpage to ensure all dynamic content is loaded.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_team_data(driver, table_xpath, is_home=True):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, table_xpath)))
        table_element = driver.find_element(By.XPATH, table_xpath + "/table")
        table_html = table_element.get_attribute('outerHTML')
        soup = BeautifulSoup(table_html, 'html.parser')
        rows = soup.find_all('tr')
        headers = ["Jersey_number", "Name", "T", "7M", "7M W%", "FT", "W%", "A", "B", "St", "2Min", "RK", "P", "P%"]
        data = []
        for row in rows[1:]:
            cols = row.find_all(['th', 'td'])
            row_data = [col.get_text(strip=True) for col in cols]
            if len(row_data) >= len(headers):
                row_data = row_data[:len(headers)]
                data.append(row_data)
        df = pd.DataFrame(data, columns=headers)
        team_type = 'Home' if is_home else 'Away'
        df['Team_Type'] = team_type
        return df
    except Exception as e:
        print(f"Error extracting team data: {e}")
        return pd.DataFrame()

def scrape_table_data(driver):
    try:
        time.sleep(5)
        date_xpath = '//*[@id="synergy-widget-fixture"]/div/div[2]/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]'
        date = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, date_xpath))).text
        home_team_xpath = '//*[@id="synergy-widget-fixture"]/div/div[2]/div/div[3]/div[3]/div[1]/div/div[2]'
        home_team = driver.find_element(By.XPATH, home_team_xpath).text
        away_team_xpath = '//*[@id="synergy-widget-fixture"]/div/div[2]/div/div[3]/div[4]/div/div[1]/div/div[2]'
        away_team = driver.find_element(By.XPATH, away_team_xpath).text
        home_table_xpath = '//*[@id="synergy-widget-fixture"]/div/div[2]/div/div[3]/div[3]/div[2]'
        home_team_df = extract_team_data(driver, home_table_xpath, is_home=True)
        home_team_df['Team'] = home_team
        home_team_df['Date'] = date
        away_table_xpath = '//*[@id="synergy-widget-fixture"]/div/div[2]/div/div[3]/div[4]/div/div[2]'
        away_team_df = extract_team_data(driver, away_table_xpath, is_home=False)
        away_team_df['Team'] = away_team
        away_team_df['Date'] = date
        combined_df = pd.concat([home_team_df, away_team_df], ignore_index=True)
        time.sleep(5)
        return combined_df, date, home_team, away_team
    except Exception as e:
        print(f"Error scraping table data: {e}")
        return pd.DataFrame(), "", "", ""

def save_to_csv(df, file_path):
    try:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        df.to_csv(file_path, index=False)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def sanitize_filename(filename):
    # Replace invalid characters in file names with an underscore
    return re.sub(r'[\/:*?"<>|\n]', '_', filename)

def main(fixtures_df):
    driver = setup_driver()
    
    for index, row in fixtures_df.iterrows():
        fixture_id = row['Fixtureid']
        match_url = f"https://www.daikin-hbl.de/de/match/{fixture_id}"
        
        driver.get(match_url)
        scroll_page(driver)
        df, date, home_team, away_team = scrape_table_data(driver)
        
        if not df.empty:
            # Construct dynamic file name based on date and team names
            clean_date = date.replace("/", "-").replace(":", "-").replace(" ", "_")
            file_name = f"{clean_date}_{home_team}_vs_{away_team}.csv"
            
            # Sanitize file name to remove invalid characters
            sanitized_file_name = sanitize_filename(file_name)
            file_path = os.path.join(r'C:\Users\Boy Cakaraningrat\Documents\GitHub\Bundesh_Dasboard\Bundesh League', sanitized_file_name)
            
            save_to_csv(df, file_path)
        else:
            print(f"No data scraped for match {fixture_id}")

    driver.quit()

if __name__ == "__main__":
    # Load the DataFrame that contains the fixture IDs
    file_path = r'C:\Users\Boy Cakaraningrat\Documents\GitHub\Bundesh_Dasboard\updated.csv'
    final_competitors_df = pd.read_csv(file_path)
    
    # Call the main function to loop through fixtures and scrape
    main(final_competitors_df)
