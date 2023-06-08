source .env

# Undeploy PVC
kubectl delete -f resources/db/postgresml-cluster-pvc.yaml -n ${DATA_E2E_POSTGRESML_NS}

# Uninstall Postgres instance
helm uninstall postgresml-bitnami -n ${DATA_E2E_POSTGRESML_NS}