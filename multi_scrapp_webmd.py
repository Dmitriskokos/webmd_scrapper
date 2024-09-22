import os
import csv
import time
import random
import logging
import winsound  
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from queue import Queue
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройки прокси
PROXY_LIST = [
    "198.44.255.5:80",
    "209.159.153.21:29185",
    "163.172.137.227:16379",
    "47.254.16.71:5008",
    "66.29.128.245:47426",
    "207.244.254.27:1208",
    "67.213.210.61:50834",
    "209.159.153.19:59552",
    "67.213.210.61:62523",
    "212.83.143.211:61596",
    "162.210.197.69:56284",
    "209.159.153.21:26778",
    "209.159.153.22:53690",
    "162.210.197.69:57158",
    "162.210.197.91:52703",
    "67.213.212.47:47863",
    "67.213.212.50:43535",
    "198.44.255.5:80",
    "23.105.170.30:30119",
    "199.204.248.124:54531",
]

csv_links_file = "output.csv"
csv_filename = "doctor_data.csv"
failed_links_file = "failed_links.csv"
dead_proxies_file = "dead_proxies.csv"
progress_file = "progress.csv"
images_folder = "images"

# Создаем папку для изображений
if not os.path.exists(images_folder):
    os.makedirs(images_folder)

# Инициализация CSV-файла с заголовками
def initialize_csv():
    if not os.path.exists(csv_filename):
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Doctor URL", "Name", "Specialty", "Address", "City", "State", "Zipcode", "Phone", "Title", "Description",
                "Book Online", "Website", "Image Name", "Experience", "Languages", "Conditions Treated",
                "Procedures Performed", "Insurance Plans", "Hospitals", "Certifications"
            ])

# Запись данных о врачах
def save_doctor_data(data):
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)

# Запись ссылки в файл с неудачными попытками
def save_failed_link(link):
    with open(failed_links_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([link])

# Запись мертвых прокси
def save_dead_proxy(proxy):
    with open(dead_proxies_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([proxy])

# Чтение мертвых прокси
def load_dead_proxies():
    if not os.path.exists(dead_proxies_file):
        return []
    with open(dead_proxies_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        return [row[0] for row in reader]

# Удаление успешно обработанных ссылок из failed_links.csv
def remove_processed_failed_links(successful_links):
    if os.path.exists(failed_links_file):
        with open(failed_links_file, mode='r', newline='', encoding='utf-8') as file:
            links = [row[0] for row in csv.reader(file) if row[0] not in successful_links]
        with open(failed_links_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for link in links:
                writer.writerow([link])

# Сохранение текущего прогресса
def save_progress(link):
    with open(progress_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([link])

# Получаем случайный прокси, исключая мертвые
def get_random_proxy(dead_proxies):
    available_proxies = [proxy for proxy in PROXY_LIST if proxy not in dead_proxies]
    if not available_proxies:
        return None  # Если все прокси мертвы, возвращаем None
    return random.choice(available_proxies)

# Настройка браузера с прокси
def setup_browser_with_proxy(dead_proxies):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    proxy = get_random_proxy(dead_proxies)
    if not proxy:
        return None  # Если нет доступных прокси, возвращаем None
    chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(options=chrome_options)
    driver.proxy_address = proxy
    return driver

# Функция для получения уникального имени файла
def get_unique_image_name(image_name):
    base_name, extension = os.path.splitext(image_name)
    unique_name = image_name
    counter = 1
    while os.path.exists(os.path.join(images_folder, unique_name)):
        unique_name = f"{base_name}-{counter}{extension}"
        counter += 1
    return unique_name

# Функция для парсинга данных врача
def parse_doctor_info(driver, link):
    try:
        driver.get(link)
        time.sleep(5)  # Увеличил время ожидания для загрузки страницы

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Извлекаем необходимые данные
        name = soup.find("h1", class_="provider-full-name loc-co-fname").text.strip() if soup.find("h1", class_="provider-full-name loc-co-fname") else "N/A"
        title = soup.find("meta", {"property": "og:title"})['content'] if soup.find("meta", {"property": "og:title"}) else "N/A"
        description = soup.find("meta", {"property": "og:description"})['content'] if soup.find("meta", {"property": "og:description"}) else "N/A"
        
        # Извлекаем телефон
        phone = None
        phone_element = soup.find("a", class_="loc-co-tpphn") or soup.find("span", class_="loc-coi-telep")
        if phone_element:
            phone = phone_element.text.strip()

        # Адрес
        address = soup.find("div", class_="webmd-row location-address loc-coi-locad").text.strip() if soup.find("div", class_="webmd-row location-address loc-coi-locad") else "N/A"
        city = soup.find("span", class_="location-city loc-coi-loccty").text.strip() if soup.find("span", class_="location-city loc-coi-loccty") else "N/A"
        state = soup.find("span", class_="location-state loc-coi-locsta").text.strip() if soup.find("span", class_="location-state loc-coi-locsta") else "N/A"
        zipcode = soup.find("span", class_="location-zipcode loc-coi-loczip").text.strip() if soup.find("span", class_="location-zipcode loc-coi-loczip") else "N/A"

        # Специальности
        specialties = ', '.join([spec.text.strip() for spec in soup.find_all("span", class_="prov-specialty-name")])

        # Опыт
        experience = soup.find("div", class_="years-of-exp").text.strip() if soup.find("div", class_="years-of-exp") else "N/A"

        # Языки
        languages = 'N/A'
        languages_header = soup.find("h2", class_="languagesCardHeader")
        if languages_header:
            languages_list = languages_header.find_next("ul", class_="languages-list")
            languages = ', '.join([lang.text.strip() for lang in languages_list.find_all("li")]) if languages_list else 'N/A'

        # Условия лечения (CONDITIONS TREATED)
        conditions = 'N/A'
        conditions_list = soup.find("ul", class_="conditions-list")
        if conditions_list:
            all_conditions = [cond.text.strip() for cond in conditions_list.find_all("li")]
            conditions = ', '.join(all_conditions)
            

        # Услуги и процедуры (видимые и скрытые элементы)
        procedures = 'N/A'
        procedures_list = soup.find("ul", class_="conditions-list")
        if procedures_list:
            all_procedures = [proc.text.strip() for proc in procedures_list.find_all("li")]
            procedures = ', '.join(all_procedures)

        # Страховые планы
        insurance_plans = 'N/A'
        insurance_section = soup.find("div", class_="insurance-content insurance-data")
        if insurance_section:
            insurance_list = insurance_section.find("ul", class_="insuranceplans")
            if insurance_list:
                all_insurance = [plan.text.strip() for plan in insurance_list.find_all("li")]
                insurance_plans = ', '.join(all_insurance)

        # Образование и сертификации (CERTIFICATIONS)
        certifications = []
        education_sections = soup.find_all("div", class_="webmd-row education-header")
        for section in education_sections:
            section_name = section.text.strip()
            institutions = section.find_next_siblings("div", class_="education-wrapper")
            institution_names = [inst.find("div", class_="school").text.strip() for inst in institutions]
            if institution_names:
                certifications.append(f"{section_name} - {', '.join(institution_names)}")

        certifications_text = ', '.join(certifications) if certifications else "N/A"

        # Госпитали (HOSPITALS)
        hospitals = 'N/A'
        hospital_section = soup.find("ul", class_="conditions-list loc-coi-hospi")
        if hospital_section:
            hospital_names = []
            for hospital_item in hospital_section.find_all("li"):
                span = hospital_item.find("span")
                a_tag = hospital_item.find("a")
                if span:
                    hospital_names.append(span.text.strip())
                elif a_tag:
                    hospital_names.append(a_tag.text.strip())
            hospitals = ', '.join(hospital_names)

        # Ссылка на картинку и загрузка
        image_url = None
        img_element = soup.find("div", class_="prov-img with-url")
        if img_element:
            img_tag = img_element.find("img", class_="loc-co-provim")
            if img_tag and img_tag['src']:
                image_url = img_tag['src']

        image_name = None
        if image_url:
            image_url = image_url.split("?")[0]  # Берем изображение в исходном разрешении
            image_name = image_url.split("/")[-1]
            unique_image_name = get_unique_image_name(image_name)
            image_path = os.path.join(images_folder, unique_image_name)
            if not os.path.exists(image_path):
                download_image(image_url, image_path)

        # Кнопка "Book Online"
        book_online_element = soup.find("span", class_="icon-request")
        book_online_url = None
        if book_online_element:
            parent_link = book_online_element.find_parent("a", href=True)
            if parent_link:
                book_online_url = parent_link['href']

        # Ссылка на сайт
        website = 'N/A'
        website_element = soup.find("a", class_="site-exit-modal", href=True)
        if website_element and 'Visit Website' in website_element.text:
            website = website_element['href']

        # Финальные данные
        doctor_data = [
            link, name, specialties, address, city, state, zipcode, phone, title, description, book_online_url, 
            website, unique_image_name, experience, languages, conditions, procedures, insurance_plans, hospitals, certifications_text
        ]
        
        logging.info(f"Спарсены данные для {name}")
        save_progress(link)
        return doctor_data

    except Exception as e:
        logging.error(f"Ошибка при парсинге {link} с прокси {driver.proxy_address}: {str(e)}")
        return None

# Скачивание изображения
def download_image(url, path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            logging.info(f"Изображение сохранено: {path}")
        else:
            logging.error(f"Ошибка скачивания изображения {url}")
    except Exception as e:
        logging.error(f"Ошибка при скачивании изображения {url}: {str(e)}")

# Основная функция для обработки ссылок
def worker_thread(driver, link_queue, dead_proxies):
    successful_links = []
    while not link_queue.empty():
        link = link_queue.get()
        doctor_data = parse_doctor_info(driver, link)
        if doctor_data:
            save_doctor_data(doctor_data)
            successful_links.append(link)
        else:
            logging.error(f"Прокси сервер {driver.proxy_address} мертв, перезапуск браузера с новым прокси")
            save_failed_link(link)
            dead_proxies.append(driver.proxy_address)
            save_dead_proxy(driver.proxy_address)
            driver.quit()
            new_driver = setup_browser_with_proxy(dead_proxies)  # Перезапуск браузера с новым прокси
            if not new_driver:
                logging.error("Все прокси мертвы. Завершение работы.")
                winsound.Beep(1000, 2000)  # Издание звукового сигнала, если все прокси мертвы
                break
            else:
                driver = new_driver  # Переназначаем браузер для продолжения работы
        link_queue.task_done()
    return successful_links

# Загрузка всех ссылок из CSV
def load_links_from_csv():
    links = []
    try:
        with open(csv_links_file, mode="r", newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                links.append(row[0])  # Считываем только ссылки
    except Exception as e:
        logging.error(f"Ошибка при загрузке ссылок из CSV: {str(e)}")
    
    return links

# Загрузка прогресса
def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, mode="r", newline='', encoding='utf-8') as file:
            last_processed = file.readline().strip()
            return last_processed
    return None

# Загрузка ссылок из failed_links.csv
def load_failed_links():
    if os.path.exists(failed_links_file):
        with open(failed_links_file, mode="r", newline='', encoding='utf-8') as file:
            return [row[0] for row in csv.reader(file)]
    return []

# Основной блок
if __name__ == "__main__":
    initialize_csv()
    all_links = load_links_from_csv()
    
    # Проверка прогресса
    last_processed_link = load_progress()
    if last_processed_link:
        all_links = all_links[all_links.index(last_processed_link) + 1:]  # Продолжаем с последней необработанной ссылки

    link_queue = Queue()
    for link in all_links:
        link_queue.put(link)

    dead_proxies = load_dead_proxies()  # Загружаем мертвые прокси
    drivers = [setup_browser_with_proxy(dead_proxies) for _ in range(8)]  # Настраиваем 8 браузеров
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker_thread, driver, link_queue, dead_proxies) for driver in drivers]
        successful_links = []
        for future in as_completed(futures):
            successful_links += future.result()

    # Закрытие всех браузеров после завершения
    for driver in drivers:
        driver.quit()

    logging.info("Все данные о врачах успешно обработаны и сохранены в CSV файл.")

    # Обработка failed_links.csv после основного парсинга
    failed_links = load_failed_links()
    if failed_links:
        logging.info("Обработка неудачных ссылок...")
        link_queue = Queue()
        for link in failed_links:
            link_queue.put(link)

        drivers = [setup_browser_with_proxy(dead_proxies) for _ in range(8)]
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker_thread, driver, link_queue, dead_proxies) for driver in drivers]
            for future in as_completed(futures):
                successful_links += future.result()

        # Закрытие всех браузеров после завершения
        for driver in drivers:
            driver.quit()

        # Удаляем обработанные ссылки из failed_links.csv
        remove_processed_failed_links(successful_links)

    logging.info("Парсинг завершен.")

    # Сохраняем мертвые прокси
    for proxy in dead_proxies:
        save_dead_proxy(proxy)

