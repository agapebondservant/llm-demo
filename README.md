# LLMOps Demo with TAP, postgresml, Argo Workflows and MLflow

## Contents
1. [Set up access control/credentials](#accesscontrol)
2. [Set up web crawler](#crawler)
3. [Deploy Bitnami Postgres on Kubernetes](#pg4k8s)
4. [Set up HuggingFace model repo](#huggingfacerepo)
5. [Integrate HuggingFace model with DataHub](#datahub)

### Set up access control/credentials<a name="accesscontrol"/>
```
source .env
tanzu secret registry delete registry-credentials -n default -y || true
tanzu secret registry add registry-credentials --username ${DATA_E2E_REGISTRY_USERNAME} --password ${DATA_E2E_REGISTRY_PASSWORD} --server https://index.docker.io/v1/ --export-to-all-namespaces --yes -ndefault
kubectl apply -f config/tap-rbac.yaml -ndefault
kubectl apply -f config/tap-rbac-2.yaml -ndefault
```

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
-[ ] helm

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
scripts/delete-postgresml-cluster.sh
```

### Set up HuggingFace model repo<a name="huggingfacerepo"/>
#### Prequisites:
- [ ] git-lfs
- [ ] Set up SSH Key for account <DATA_E2E_HUGGINGFACE_USERNAME>: <a href="https://huggingface.co/settings/keys" target="_blank">link</a>

1. Set up repo:
```
export REPO_NAME=<your repo name>
scripts/create-huggingface-model-repo.sh $REPO_NAME
```

2. Publish a model to the repo:
```
scripts/save-dummy-huggingface-model.sh $REPO_NAME
```

### Integrate HuggingFace model with DataHub<a name="datahub"/>
1. Run DataHub Metadata Emitter:
```
$(which python3.9)  -c "from app import datahub_emitter; import os; datahub_emitter.send_metadata('tanzuhuggingface/dev', \
                             'nlp', \
                              'DEV', \
                              os.getenv('DATA_E2E_DATAHUB_GMS_URL'), \
                              'Fine-tuned DistilBERT model')"
```
2. Set up Argo Workflows (if not already setup):

* Set up secrets:
```
source .env
tanzu secret registry delete registry-credentials -n default -y || true
tanzu secret registry add registry-credentials --username ${DATA_E2E_REGISTRY_USERNAME} --password ${DATA_E2E_REGISTRY_PASSWORD} --server https://index.docker.io/v1/ --export-to-all-namespaces --yes -ndefault
kubectl apply -f resources/appcr/tap-rbac.yaml -ndefault
kubectl apply -f resources/appcr/tap-rbac-2.yaml -ndefault
```

* Set up Argo Workflows (if not already setup):
```
source .env
kubectl create ns argo
kubectl apply -f resources/argo/argo-workflow.yaml -nargo
envsubst < resources/argo/argo-workflow-http-proxy.in.yaml > resources/argo/argo-workflow-http-proxy.yaml
kubectl apply -f resources/argo/argo-workflow-http-proxy.yaml -nargo
kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=argo:default -n argo
kubectl apply -f resources/argo/argo-workflow-rbac.yaml -nargo
```

* To login to Argo, copy the token from here:
```
kubectl -n argo exec $(kubectl get pod -n argo -l 'app=argo-server' -o jsonpath='{.items[0].metadata.name}') -- argo auth token
```

3. Set up GitOps sync hook with kappcontroller's App CR:
```
kapp deploy -a huggingface-tanzudev-monitor-<THE PIPELINE ENVIRONMENT> -f resources/appcr/pipeline_app.yaml --logs -y  -nargo
```

4. View progress:
```
kubectl get app huggingface-tanzudev-monitor-<THE PIPELINE ENVIRONMENT> -oyaml  -nargo
```

* To delete the pipeline:
```
kapp delete -a huggingface-tanzudev-monitor-<THE PIPELINE ENVIRONMENT> -y -nargo
```
