# webmd_scrapper
Multi-Threaded Web Scraper for Doctor Profiles with Cloudflare Bypass and Proxy Rotation



**Description**:  

This Python-based scraper is designed for efficient extraction of detailed doctor profiles from WebMD while bypassing Cloudflare protection and CAPTCHA. With multi-threading and intelligent proxy management, this tool ensures uninterrupted scraping and handles failures gracefully. Each feature is crafted to handle high-scale data extraction while minimizing blocks or interruptions.

---

### **Key Features:**

#### **Cloudflare Bypass and CAPTCHA Handling**  
- Automatically bypasses Cloudflare protection and CAPTCHA challenges using rotating proxies, allowing uninterrupted data extraction from WebMD without triggering access restrictions.

#### **Multi-Threaded Scraping**  
- Supports up to 8 simultaneous browser instances for fast, concurrent scraping of multiple profiles, ensuring the process is completed efficiently.

#### **Proxy Rotation & Dead Proxy Management**  
- Rotates through a list of proxies to prevent IP bans and detection.
- Automatically detects and records dead proxies in `dead_proxies.csv` for exclusion from future use.
- If all proxies are dead, the remaining live proxies will be reused across all active browser sessions, ensuring the scraping continues without interruptions.

#### **Automatic Browser Restart on Failure**  
- If a browser session fails due to proxy issues, the browser is restarted with a new proxy. Failed attempts are logged, and the scraper seamlessly resumes with the next available link.

#### **Link Failure Management**  
- Links that failed to load properly are stored in `failed_links.csv` for later retry, ensuring no data is lost.

#### **Progress Saving and Resumption**  
- The scraper saves its progress in `progress.csv`, allowing it to resume from the last processed link if interrupted, ensuring smooth recovery without duplicating work.

#### **Detailed Data Extraction**  
- Extracts comprehensive doctor profiles, including:
  - Name, specialty, contact details, address.
  - Conditions treated, procedures performed, certifications, hospitals affiliated with.
  - Links for online booking and official websites.
  - Profile images, which are downloaded and saved locally.

#### **Image Downloading**  
- Automatically downloads and saves doctor profile images to the local `images/` folder, ensuring a complete dataset.

### `requirements.txt`:

Here’s the content for your `requirements.txt` file that includes all the necessary dependencies for your WebMD scraping script:

```
selenium==4.5.0
beautifulsoup4==4.11.1
requests==2.27.1
lxml==4.9.1
```



### Recent Changes

1. **New headless browser mode:** The script now uses the new headless mode (`--headless=new`) to prevent the browser windows from appearing while still maintaining full functionality.
   
2. **Browser windows are hidden:** The `--window-position=-32000,-32000` option has been added to ensure that browser windows are completely hidden and do not interfere with the desktop environment.

3. **Active browser monitoring:** A counter has been added to log the number of active browser instances. After each successful scrape, the log will display the number of currently running browsers, allowing for easier detection of browser failures or issues.

4. **Proxy handling optimization:** Improved logic for handling proxy servers to prevent errors when running in headless mode.

### Installation and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/webmd-multi-scraper.git
   cd webmd-multi-scraper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your proxies to the `PROXY_LIST` in the main script file.

4. Run the script:
   ```bash
   python multi_scrapp_webmd.py
   ```

### Logging

Example of script logs:
```
2024-09-22 23:05:08,599 - INFO - Image saved: images\photo-5906.jpg
2024-09-22 23:05:08,599 - INFO - Scraped data for Dr. James Joseph Mahoney, MD
2024-09-22 23:05:08,599 - INFO - Currently (10) browsers are running
```

### Important Notes

- Keep the proxy list up to date. The script will automatically restart the browsers when issues with proxies are detected.
- The script also automatically saves failed links to a separate file for future processing.

### License

This project is licensed under the MIT License.


