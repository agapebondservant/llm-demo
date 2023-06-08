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
#### Prequisites:
[] helm

1. Build the postgresml-enabled Postgres instance image
   (NOTE: Skip if already built; 
    also, must build on a network with sufficient bandwidth - example, might run into issues behind some VPNs):
```
source .env
scripts/build-postgresml-baseimage.sh
watch kubectl get pvc -n ${DATA_E2E_POSTGRESML_NS}
```

2. Deploy Postgres instance:
```
scripts/deploy-postgresml-cluster.sh
watch kubectl get all -n ${DATA_E2E_POSTGRESML_NS}
```

3. To get the connect string for the postgresml-enabled instance:
```
export POSTGRESML_PW=$(kubectl get secret postgresml-db-secret -n postgresml -ojsonpath='{.data.password }' | base64 --decode)
export POSTGRESML_ENDPOINT=$(kubectl get svc postgresml -npostgresml -o jsonpath="{.status.loadBalancer.ingress[0].hostname}")
echo postgresql://pgadmin:${POSTGRESML_PW}@${POSTGRESML_ENDPOINT}/postgresml?sslmode=require
```

4. To delete the Postgres instance:
```
script/delete-postgresml-cluster.sh
```