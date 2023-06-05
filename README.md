# LLMOps Demo with TAP, postgresml, Argo Workflows and MLflow

## Contents
1. [Set up web crawler](#crawler)
2. [Deploy Bitnami Postgres on Kubernetes](#pg4k8s)

### Set up web crawler<a name="crawler"/>

1. To set up host machine for WebCrawler (Mac):
```
Download Chrome Driver: https://chromedriver.chromium.org/downloads
chmod +x /Users/oawofolu/Downloads/chromedriver_mac64/chromedriver
sudo cp /Users/oawofolu/Downloads/chromedriver_mac64/chromedriver /usr/local/bin
sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

2. Test crawler for OneDrive folder:
```
LLM_DEMO_EMAIL=oawofolu@vmware.com \
BASE_URL='https://onevmw.sharepoint.com' \
FINAL_URL='https://onevmw.sharepoint.com/:f:/r/teams/TSL-v20/Shared%20Documents/Tanzu%20AI%20-%20ML/Demos/LLM%20Demo/docs?csf=1&web=1&e=m67rNF' \
$(which python3.9) -c "import os; from app import crawler; crawler.scrape_url(base_url_path=os.environ['BASE_URL'], redirect_url_path=os.environ['FINAL_URL'])"
```         

### Deploy Bitnami Postgres on Kubernetes<a name="pg4k8s"/>