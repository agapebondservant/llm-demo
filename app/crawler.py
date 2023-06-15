import pdfbox
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import requests
import os
from urllib.parse import urlparse, unquote, quote
from pypdf import PdfReader
from dotenv import load_dotenv
from app import data_loader

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

load_dotenv()


def extract_text_from_pdf(file_path: str):
    """
    Extracts text from the given pdf file.
    :param file_path: Location of the pdf file
    :return: Content of the pdf (as text)
    """
    extracted_file_path = file_path.replace('.pdf', '.txt')
    p = pdfbox.PDFBox()
    p.extract_text(file_path)
    with open(extracted_file_path, 'r') as handle:
        return handle.read()


def extract_metadata_from_pdf(file_path: str):
    """
    Extracts text and metadata from the given pdf file as a PyPdf object.
    :param file_path: Location of the pdf file
    :return: Dictionary representing the pdf
    """
    reader = PdfReader(file_path)
    pages = reader.pages
    info = reader.metadata
    number_of_pages = len(pages)
    data = {**{'/NumberOfPages': number_of_pages}, **info}
    return data


def scrape_url(base_url_path: str, redirect_url_path: str, experiment_name='scraper'):
    """
    Scrapes the provides Sharepoint URL for pdf links.
    :param experiment_name: MLflow experiment that this task will be associated with
    :param base_url_path: Base domain of the Sharepoint folder to scrape (ex. http://onevmw.sharepoint.com)
    :param redirect_url_path: Full URL of the Sharepoint folder to scrape
    :return: A list of locations of the downloaded files
    """
    wait = WebDriverWait(driver, 30)
    driver.get("https://onedrive.live.com/about/en-us/signin/")

    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "SignIn")))
    email = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.form-group > input.form-control")))
    email.send_keys(os.environ['LLM_DEMO_EMAIL'])

    submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
    submit.click()
    WebDriverWait(driver, timeout=120, poll_frequency=5).until(EC.url_contains("onevmw"))

    driver.get(redirect_url_path)
    links = find_and_download_pdf_links(base_url_path, 'docs')

    for link in links:
        logger.info(f"Extracting text from pdf files...{link}")
        extracted_text = extract_text_from_pdf(link)
        data_loader.store_tokens(link, extracted_text, experiment_name)

    driver.quit()
    return links is not None


def find_and_download_pdf_links(base_url_path: str, download_path: str):
    """
    Searches for all pdf links in the provided Sharepoint URL
    :param base_url_path: Base domain of the Sharepoint folder to search (ex. http://onevmw.sharepoint.com)
    :param download_path: Local target directory where files will be downloaded to
    :return: List of downloaded pdf files
    """
    scripts = driver.find_elements(By.XPATH, '//script[type=text/javascript]')

    for script in scripts:
        driver.execute_script('arguments[0].innerHTML', script)

    result = yaml.load(str(driver.execute_script('return g_listData')))
    logger.debug(yaml.dump(result))

    pdfs = [f"{base_url_path}{quote(row['FileRef'])}" for row in result['ListData']['Row'] if
            row['File_x0020_Type'] == 'pdf']
    docs = []

    for pdf in pdfs:
        doc_name = _get_pdf_from_url(pdf, download_path)
        docs.append(doc_name)

    logger.debug(f"Docs : {docs}")

    return docs


def _get_pdf_from_url(url_path: str, download_path: str):
    """
    Utility method which downloads a PDF file from a given URL.
    Uses cookies from the current Selenium session to prevent Unauthorized errors
    :param url_path: URL to download PDF file from
    :param download_path: Local directory where files will be downloaded
    :return: Return the download location of the PDF file
    """
    doc_name = f"{download_path}/{unquote(os.path.basename(urlparse(url_path).path))}"

    logger.info(f"Downloading pdf file...{doc_name}")

    cookies_dict = _get_cookies()

    response = requests.get(url_path, cookies=cookies_dict)
    with open(doc_name, 'wb') as doc:
        for chunk in response.iter_content(1024):
            doc.write(chunk)

    return doc_name


def _get_cookies():
    """
    Retrieves cookies from the ongoing Selenium session
    :return: Dictionary of active cookies
    :return: Dictionary of active cookies
    """
    all_cookies = driver.get_cookies()
    cookies_dict = {cookie['name']: cookie['value'] for cookie in all_cookies}
    return cookies_dict
