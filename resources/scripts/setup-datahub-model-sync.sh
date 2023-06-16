source .env
tanzu secret registry delete registry-credentials -n default -y || true
tanzu secret registry add registry-credentials --username ${DATA_E2E_REGISTRY_USERNAME} --password ${DATA_E2E_REGISTRY_PASSWORD} --server https://index.docker.io/v1/ --export-to-all-namespaces --yes -ndefault
kubectl apply -f resources/appcr/tap-rbac.yaml -n ${DATA_E2E_POSTGRESML_NS}
kubectl apply -f resources/appcr/tap-rbac-2.yaml -n ${DATA_E2E_POSTGRESML_NS}
