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

