import threading
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import logging
import os
from queue import Queue

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Прокси
PROXY_LIST = [
    "162.0.220.215:37245",
    "209.159.153.22:59778",
    "159.65.237.225:1444",
    "165.232.129.150:80",
    "38.91.106.252:43839",
    "174.138.171.162:47853",
    "209.159.153.22:64439",
    
    # Добавьте другие прокси
]

# Файл с мертвыми прокси
dead_proxy_file = "dead_proxies.csv"
dead_proxies = set()

if os.path.exists(dead_proxy_file):
    with open(dead_proxy_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            dead_proxies.add(row[0])

# Имя CSV файла с результатами
csv_filename = "doctor_urls.csv"

# Имя CSV файла с исходными ссылками
csv_links_file = "links.csv"

# Имя CSV файла с обработанными ссылками (для восстановления прогресса)
csv_processed_file = "processed_links.csv"

# Создание CSV файла и запись заголовков, если файла не существует
if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Doctor URL", "Address"])

def get_random_proxy():
    """Функция для случайного выбора прокси из списка."""
    working_proxies = [p for p in PROXY_LIST if p not in dead_proxies]
    if working_proxies:
        return random.choice(working_proxies)
    return None

def mark_proxy_as_dead(proxy):
    """Пометить прокси как мертвый и записать в файл."""
    dead_proxies.add(proxy)
    with open(dead_proxy_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([proxy])
    logging.info(f"Мертвый прокси добавлен в dead_proxies.csv: {proxy}")

def setup_browser_with_proxy():
    """Настройка браузера с использованием прокси."""
    chrome_options = Options()
    chrome_options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")

    # Получаем случайный прокси из списка
    proxy = get_random_proxy()
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
        logging.info(f"Используем прокси: {proxy}")

    driver = webdriver.Chrome(options=chrome_options)
    return driver, proxy

def save_links_to_csv(links, filename="doctor_urls.csv"):
    """Сохранение ссылок врачей в CSV файл после каждой страницы."""
    try:
        with open(filename, mode="a", newline="", encoding='utf-8') as file:
            writer = csv.writer(file)
            for link, address in links:
                writer.writerow([link, address])
        logging.info(f"Успешно сохранено {len(links)} ссылок врачей в {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении CSV: {e}")

def save_processed_link(link, page, filename="processed_links.csv"):
    """Сохранение обработанной ссылки для восстановления прогресса."""
    try:
        with open(filename, mode="a", newline="", encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([link, page])
        logging.info(f"Сохранена обработанная ссылка: {link} на странице {page}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении обработанной ссылки: {e}")

def extract_urls_from_page(soup):
    """Извлечение всех URL и адресов врачей на странице."""
    urls = []
    
    # Ищем все элементы с врачами
    doctor_elements = soup.find_all("a", class_="prov-name")
    
    for doctor_element in doctor_elements:
        # Извлекаем URL врача
        url = doctor_element.get("href")
        
        # Извлекаем адрес врача
        address_element = doctor_element.find_next("span", class_="addr-text")
        address = address_element.text.strip() if address_element else "Адрес не найден"
        
        urls.append((url, address))
    
    return urls

def extract_and_save_urls(base_url, start_page=1, max_links=500):
    """Функция для извлечения и сохранения URL на странице с ограничением в 500 ссылок."""
    driver = None
    total_doctors = 0  # Счетчик врачей
    current_page = start_page

    while total_doctors < max_links:
        try:
            driver, proxy = setup_browser_with_proxy()  # Используем браузер с прокси
            driver.get(f"{base_url}?page={current_page}")
            logging.info(f"Открыта базовая страница: {base_url}, страница {current_page}")

            while total_doctors < max_links:
                time.sleep(3)  # Добавляем небольшую задержку, чтобы избежать блокировок
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                current_page_urls = extract_urls_from_page(soup)
                logging.info(f"Найдено {len(current_page_urls)} URL на текущей странице.")

                if current_page_urls:
                    save_links_to_csv(current_page_urls)
                    total_doctors += len(current_page_urls)
                    save_processed_link(base_url, current_page)
                    if total_doctors >= max_links:
                        logging.info(f"Достигнут лимит в {max_links} врачей для {base_url}.")
                        break

                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-next[title='Next Page']"))
                    )
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    logging.info(f"Переход на следующую страницу {current_page}.")
                except (NoSuchElementException, TimeoutException):
                    logging.info(f"Достигнута последняя страница для {base_url}.")
                    break

        except WebDriverException as e:
            logging.error(f"Ошибка с прокси {proxy}: {e}. Пробую следующий прокси.")
            mark_proxy_as_dead(proxy)
        except Exception as e:
            logging.error(f"Ошибка при работе с сайтом: {e}")
        finally:
            if driver:
                driver.quit()

def load_links_from_csv(filename="links.csv"):
    """Загрузка ссылок из CSV файла."""
    links = []
    try:
        with open(filename, mode="r", newline="", encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                links.append(row[0])  # Предполагаем, что ссылки находятся в первом столбце
    except Exception as e:
        logging.error(f"Ошибка при загрузке CSV: {e}")
    return links

def load_processed_links(filename="processed_links.csv"):
    """Загрузка уже обработанных ссылок и страниц для восстановления прогресса."""
    processed_links = {}
    if os.path.exists(filename):
        try:
            with open(filename, mode="r", newline="", encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    processed_links[row[0]] = int(row[1])  # ссылка и страница
        except Exception as e:
            logging.error(f"Ошибка при загрузке обработанных ссылок: {e}")
    return processed_links

# Загрузка всех ссылок и уже обработанных ссылок
all_links = load_links_from_csv(csv_links_file)
processed_links = load_processed_links(csv_processed_file)

# Фильтрация ссылок, которые еще не были обработаны
remaining_links = [(link, processed_links.get(link, 1)) for link in all_links if link not in processed_links]

# Функция для обработки очереди ссылок
def worker_thread(link_queue):
    """Работник потока, который обрабатывает список ссылок."""
    while not link_queue.empty():
        link, start_page = link_queue.get()
        extract_and_save_urls(link, start_page=start_page)
        link_queue.task_done()

# Очередь для ссылок
link_queue = Queue()

# Добавление оставшихся ссылок в очередь с учетом страницы пагинации
for link, start_page in remaining_links:
    link_queue.put((link, start_page))

# Количество потоков
num_threads = 5

# Создание и запуск потоков
threads = []
for i in range(num_threads):
    thread = threading.Thread(target=worker_thread, args=(link_queue,))
    threads.append(thread)
    thread.start()

# Ожидание завершения всех потоков
for thread in threads:
    thread.join()

logging.info("Все URL-адреса обработаны и сохранены в CSV файл.")

