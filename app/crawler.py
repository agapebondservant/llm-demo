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
# options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="114.0.5735.90").install()), options=options)

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


def scrape_sharepoint_url(base_url_path: str, redirect_url_path: str, experiment_name='scraper'):
    """
    Scrapes the provided Sharepoint URL for pdf links.
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
    links, files = find_and_download_pdf_links(base_url_path, redirect_url_path, 'docs')

    for idx, file in enumerate(files):
        logger.info(f"Extracting text from pdf files...{file}")
        extracted_text = extract_text_from_pdf(file)
        data_loader.store_tokens(links[idx], extracted_text, experiment_name)

    driver.quit()
    return links is not None


def scrape_slack_url(env_file_path: str, cookies_file_path: str, experiment_name='scraper'):
    """
    Scrapes the provided Slack channel(s).
    :param env_file_path: Path to the environment file to use for scraping
    :param cookies_file_path: Path to the cookies file to use for scraping
    :param experiment_name: MLflow experiment that this task will be associated with
    :return: A list of links to the scraped conversations
    """

    # TODO: Use python libraries instead of a subprocess
    # os.system(f'resources/scripts/scrape-slack.sh {cookies_file_path} ../{env_file_path}')

    dirpath = 'slack-data'
    files = os.listdir(dirpath)
    for f in files:
        if f.endswith('json'):
            filename = os.path.abspath(os.path.join(dirpath, f))
            logger.info(f"Extracting text from json file...{filename}")
            extracted_json = os.popen(f"jq -c '.' {filename}").read()
            data_loader.store_tokens(f, extracted_json, experiment_name, loader_function_name='run_json_loader_task')


def find_and_download_pdf_links(base_url_path: str, redirect_url_path: str, download_path: str):
    """
    Searches for all pdf links in the provided Sharepoint URL
    :param base_url_path: Base domain of the Sharepoint folder to search (ex. http://onevmw.sharepoint.com)
    :param redirect_url_path: Full URL of the Sharepoint folder to scrape
    :param download_path: Local target directory where files will be downloaded to
    :return: List of downloaded pdf files
    """
    pdfs, docs = [], []
    WebDriverWait(driver, timeout=120, poll_frequency=5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-automationid=FieldRenderer-name]")))
    tags = driver.find_elements(By.CSS_SELECTOR, "button[data-automationid=FieldRenderer-name]")
    for tag in tags:
        logger.info(f"{redirect_url_path}/{tag.get_attribute('innerText')}")
        pdfs.append(f"{redirect_url_path}/{tag.get_attribute('innerText')}")

    for pdf in pdfs:
        doc_name = _get_pdf_from_url(pdf, download_path)
        docs.append(doc_name)

    logger.debug(f"Docs : {docs}\nLinks: {pdfs}")

    return pdfs, docs


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
