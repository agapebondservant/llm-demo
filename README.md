# LLMOps Demo with TAP, postgresml, Argo Workflows and MLflow

## Contents
1. [Install required Python libraries](#pythonlib)
2. [Set up access control/credentials](#accesscontrol)
3. [Set up web crawler](#crawler)
4. [Deploy Bitnami Postgres on Kubernetes](#pg4k8s)
5. [Set up Training and Test Dbs](#traintestdbs)
6. [Generate embeddings](#embeddings)
7. [Set up HuggingFace model repo](#huggingfacerepo)
8. [Integrate HuggingFace model with DataHub](#datahub)
9. [Deploy Demo app](#demoapp)

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
source .env;
export LB_ENDPOINT=$(kubectl get svc postgresml-bitnami-postgresql -n ${DATA_E2E_POSTGRESML_NS} -o jsonpath="{.status.loadBalancer.ingress[0].hostname}");
export DATA_E2E_LLMAPP_TRAINING_DB_URI=postgresql://postgres:${DATA_E2E_BITNAMI_AUTH_PASSWORD}@${LB_ENDPOINT}:5432/${DATA_E2E_BITNAMI_AUTH_DATABASE};sslmode=allow;
LLM_DEMO_EMAIL=oawofolu@vmware.com \
BASE_URL='https://onevmw.sharepoint.com' \
FINAL_URL='https://onevmw.sharepoint.com/:f:/r/teams/TSL-v20/Shared%20Documents/Tanzu%20AI%20-%20ML/Demos/LLM%20Demo/docs?csf=1&web=1&e=m67rNF' \
$(which python3) -c "import os; from app import crawler; crawler.scrape_url(base_url_path=os.environ['BASE_URL'], redirect_url_path=os.environ['FINAL_URL'], experiment_name='scraper12333')"
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
