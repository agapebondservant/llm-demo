# LLMOps Demo with TAP, postgresml, Argo Workflows and MLflow

This is an accelerator that can be used to generate an end-to-end LLM application on TAP.

* Install App Accelerator: (see https://docs.vmware.com/en/Tanzu-Application-Platform/1.0/tap/GUID-cert-mgr-contour-fcd-install-cert-mgr.html)
```
tanzu package available list accelerator.apps.tanzu.vmware.com --namespace tap-install
tanzu package install accelerator -p accelerator.apps.tanzu.vmware.com -v 1.0.1 -n tap-install -f resources/app-accelerator-values.yaml
Verify that package is running: tanzu package installed get accelerator -n tap-install
Get the IP address for the App Accelerator API: kubectl get service -n accelerator-system
```

Publish Accelerators:
```
tanzu plugin install --local <path-to-tanzu-cli> all
tanzu acc create llm-demo --git-repository https://github.com/agapebondservant/llm-demo.git --git-branch main
```

## Contents
1. [Install required Python libraries](#pythonlib)
2. [Set up access control/credentials](#accesscontrol)
3. [Set up web crawler](#web-crawler)
4. [Set up Slack crawler](#slack-crawler)
5. [Deploy Bitnami Postgres on Kubernetes](#pg4k8s)
6. [Set up SchemaSpy](#schemaspy)
7. [Set up Training and Test Dbs](#traintestdbs)
8. [Generate embeddings](#embeddings)
9. [Set up HuggingFace model repo](#huggingfacerepo)
10. [Integrate HuggingFace model with DataHub](#datahub)
11. [Set up Other Argo Pipelines](#argopipelines)
12. [Deploy Demo app](#demoapp)

### Install required Python libraries<a name="pythonlib"/>
Install required Python libraries:
```
pip install -r requirements.txt
```

### Set up access control/credentials<a name="accesscontrol"/>
```
source .env
tanzu secret registry delete registry-credentials -n default -y || true
tanzu secret registry add registry-credentials --username ${DATA_E2E_REGISTRY_USERNAME} --password ${DATA_E2E_REGISTRY_PASSWORD} --server https://index.docker.io/v1/ --export-to-all-namespaces --yes -ndefault
kubectl apply -f config/tap-rbac.yaml -ndefault
kubectl apply -f config/tap-rbac-2.yaml -ndefault
```

### Set up web crawler<a name="web-crawler"/>

1. To set up host machine for WebCrawler (Mac):
```
Download Chrome Driver: https://chromedriver.chromium.org/downloads
chmod +x /Users/oawofolu/Downloads/chromedriver_mac64/chromedriver
sudo cp /Users/oawofolu/Downloads/chromedriver_mac64/chromedriver /usr/local/bin
sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

2. Test crawler for OneDrive folder:
```
source .env;
export LB_ENDPOINT=$(kubectl get svc postgresml-bitnami-postgresql -n ${DATA_E2E_POSTGRESML_NS} -o jsonpath="{.status.loadBalancer.ingress[0].hostname}");
export DATA_E2E_LLMAPP_TRAINING_DB_URI=postgresql://postgres:${DATA_E2E_BITNAMI_AUTH_PASSWORD}@${LB_ENDPOINT}:5432/${DATA_E2E_BITNAMI_AUTH_DATABASE};sslmode=allow;
LLM_DEMO_EMAIL=oawofolu@vmware.com \
BASE_URL='https://onevmw.sharepoint.com' \
FINAL_URL='https://onevmw.sharepoint.com/:f:/r/teams/TSL-v20/Shared%20Documents/Tanzu%20AI%20-%20ML/Resources/Demos/LLM%20Demo/docs' \
$(which python3) -c "import os; from app import crawler; crawler.scrape_sharepoint_url(base_url_path=os.environ['BASE_URL'], redirect_url_path=os.environ['FINAL_URL'], experiment_name='scraper12333')"
```      

### Set up slack crawler<a name="slack-crawler"/>

1. Set up pre-requisites:
[] Chrome plugin - "Export cookie json file for Pupeteer"
[] Environment properties - Update slack/.env as appropriate for your environment

2. Set up `cookies.json` file for scraper:
```
- Navigate to `vmware.slack.com`
- Click on the "Export cookie json file for Pupeteer" option in the browser extensions
- Click on "Export cookies as JSON"
- Ensure that the following file exists: ~/Downloads/app.slack.com.cookies.json
```

3. Test slack scraper:
```
source .env
export LB_ENDPOINT=$(kubectl get svc postgresml-bitnami-postgresql -n ${DATA_E2E_POSTGRESML_NS} -o jsonpath="{.status.loadBalancer.ingress[0].hostname}");
LLM_DEMO_EMAIL=oawofolu@vmware.com \
LLM_DEMO_SLACK_ENV_PATH='resources/slack/.env' \
LLM_DEMO_COOKIES_PATH='~/Downloads/app.slack.com.cookies.json' \
$(which python3) -c "import os; from app import crawler; crawler.scrape_slack_url(env_file_path=os.environ['LLM_DEMO_SLACK_ENV_PATH'], cookies_file_path=os.environ['LLM_DEMO_COOKIES_PATH'], experiment_name='scraper99999')"
# rm -rf slack/
```   

### Deploy Bitnami Postgres on Kubernetes<a name="pg4k8s"/>
#### Prequisites:
-[ ] helm

1. Build the postgresml-enabled Postgres instance image
   (NOTE: Skip if already built; 
    also, must build on a network with sufficient bandwidth - example, might run into issues behind some VPNs):
```
source .env
cd resources/db
scripts/build-postgresml-baseimage.sh
watch kubectl get pvc -n ${DATA_E2E_POSTGRESML_NS}
cd -
```

2. Deploy Postgres instance:
```
resources/scripts/deploy-postgresml-cluster.sh
watch kubectl get all -n ${DATA_E2E_POSTGRESML_NS}
```

3. To get the connect string for the postgresml-enabled instance:
```
export POSTGRESML_PW=${DATA_E2E_BITNAMI_AUTH_PASSWORD}
export POSTGRESML_ENDPOINT=$(kubectl get svc ${DATA_E2E_BITNAMI_AUTH_DATABASE}-bitnami-postgresql -n${DATA_E2E_POSTGRESML_NS} -o jsonpath="{.status.loadBalancer.ingress[0].hostname}")
echo postgresql://postgres:${POSTGRESML_PW}@${POSTGRESML_ENDPOINT}/${DATA_E2E_BITNAMI_AUTH_DATABASE}?sslmode=require
```

4. To delete the Postgres instance:
```
resources/scripts/delete-postgresml-cluster.sh
```

### Set up SchemaSpy<a name="schemaspy"/>
1. Download schemaspy:
```
curl -L https://github.com/schemaspy/schemaspy/releases/download/v6.2.3/schemaspy-6.2.3.jar \
--output resources/db/schemaspy/schemaspy.jar
```

### Set up Training and Test Dbs<a name="traintestdbs"/>
1. Run the following to apply a new changeset to the database:
```
source .env
export DATA_E2E_LIQUIBASE_TRAINING_DB_URI=postgresql://postgresml-bitnami-postgresql.${DATA_E2E_POSTGRESML_NS}.svc.cluster.local:5432/${DATA_E2E_BITNAMI_AUTH_DATABASE};sslmode=allow \
XYZSCHEMA=public XYZCHANGESETID=`echo $(date '+%Y%m%d%H%M%s')` \
envsubst < resources/db/liquibase/setup.in.yaml > resources/db/liquibase/setup.yaml
kubectl apply -f resources/db/liquibase/setup.yaml -n ${DATA_E2E_POSTGRESML_NS}
```

2. Verify that the migration job ran without errors:
```
kubectl logs job/liquibase -n ${DATA_E2E_POSTGRESML_NS}
```

3. Verify that the new data schemas were loaded:
```
kubectl exec -it postgresml-bitnami-postgresql-0 -n ${DATA_E2E_POSTGRESML_NS} -- psql postgresql://postgres:${DATA_E2E_BITNAMI_AUTH_PASSWORD}@localhost:5432/${DATA_E2E_BITNAMI_AUTH_DATABASE}?sslmode=allow -c "SELECT id, filename, dateexecuted, orderexecuted from public.databasechangelog"
```

### Generate embeddings<a name="embeddings"/>
1. Run the following to generate embeddings from the loaded data:
```
source .env
export DATA_E2E_LIQUIBASE_TRAINING_DB_URI=postgresql://postgres:${DATA_E2E_BITNAMI_AUTH_PASSWORD}@postgresml-bitnami-postgresql.${DATA_E2E_POSTGRESML_NS}.svc.cluster.local:5432/${DATA_E2E_BITNAMI_AUTH_DATABASE};sslmode=allow \
XYZSCHEMA=public XYZCHANGESETID=`echo $(date '+%Y%m%d%H%M%s')` \
envsubst < resources/db/liquibase/embeddings.in.yaml > resources/db/liquibase/embeddings.yaml
kubectl apply -f resources/db/liquibase/embeddings.yaml -n ${DATA_E2E_POSTGRESML_NS}
```

2. Verify that the job runs without errors (NOTE - this job may take a while to complete):
```
kubectl logs job/embeddings -n ${DATA_E2E_POSTGRESML_NS} --follow
```

### Set up HuggingFace model repo<a name="huggingfacerepo"/>
#### Prequisites:
- [ ] git-lfs
- [ ] Set up SSH Key for account <DATA_E2E_HUGGINGFACE_USERNAME>: <a href="https://huggingface.co/settings/keys" target="_blank">link</a>

1. Set up repo:
```
export REPO_NAME=<your repo name>
resources/scripts/create-huggingface-model-repo.sh $REPO_NAME
```

2. Publish a model to the repo:
```
resources/scripts/save-dummy-huggingface-model-summarization.sh $REPO_NAME
```

### Integrate HuggingFace model with DataHub<a name="datahub"/>
1. Run DataHub Metadata Emitter:
```
$(which python3.9)  -c "from app.analytics import model_customization; import os; model_customization.send_metadata('tanzuhuggingface/dev', \
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
source .env
envsubst < resources/appcr/pipeline_configmap.in.yaml > resources/appcr/pipeline_configmap.yaml
kubectl delete -f resources/appcr/pipeline_configmap.yaml -n argo
kubectl apply -f resources/appcr/pipeline_configmap.yaml -n argo
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

### Set up other Argo Pipelines<a name="argopipelines"/>
1. Set up embeddings pipeline:
```
source .env
envsubst < resources/appcr/pipeline_configmap.in.yaml > resources/appcr/pipeline_configmap.yaml
kubectl delete -f resources/appcr/pipeline_configmap.yaml -n argo
kubectl apply -f resources/appcr/pipeline_configmap.yaml -n argo
kubectl delete -f resources/appcr/pipeline_embeddings.yaml -n argo
kubectl apply -f resources/appcr/pipeline_embeddings.yaml -n argo
```

2. View progress (NOTE: can also view progress in Argo UI):
```
watch kubectl get pods -n argo
```

3. Delete the pipeline:
```
kubectl delete -f resources/appcr/pipeline_embeddings.yaml -n argo
```

4. Build Docker image for huggingface setup pipeline (one-time task: only required if it has not already been pre-built):
```
source .env
cd resources/huggingface
echo -e ${DATA_E2E_LLM_REGISTRY_PASSWORD} | docker login -u ${DATA_E2E_LLM_REGISTRY_USERNAME} --password-stdin
docker build -t ${DATA_E2E_LLM_REGISTRY_USERNAME}/hugging-face-cli:latest .
docker push ${DATA_E2E_LLM_REGISTRY_USERNAME}/hugging-face-cli:latest
cd -
```

5. Set up huggingface setup pipeline: (after updating `huggingface_repo` in the `resources/appcr/values.yaml` file as appropriate):
```
ytt -f resources/appcr/pipeline_create_huggingfacerepo.yaml -f resources/appcr/values-other.yaml | kubectl delete -n argo -f -
ytt -f resources/appcr/pipeline_create_huggingfacerepo.yaml -f resources/appcr/values-other.yaml | kubectl apply -n argo -f -
```

5. View progress (NOTE: can also view progress in Argo UI):
```
watch kubectl get pods -n argo
```

6. Delete the pipeline:
```
ytt -f resources/appcr/pipeline_create_huggingfacerepo.yaml -f resources/appcr/values.yaml | kubectl delete -n argo -f -
```

### Deploy Demo app<a name="demoapp"/>
* Deploy the app:
```
source .env
envsubst < resources/tapworkloads/workload.in.yaml > resources/tapworkloads/workload.yaml
tanzu apps workload create llm-demo -f resources/tapworkloads/workload.yaml --yes
```

* Tail the logs of the main app:
```
tanzu apps workload tail llm-demo --since 64h
```

* Once deployment succeeds, get the URL for the main app:
```
tanzu apps workload get llm-demo     #should yield llm-demo.default.<your-domain>
```

* To delete the app:
```
tanzu apps workload delete llm-demo --yes
```
