source .env

# Uninstall Postgres instance
helm uninstall ${DATA_E2E_BITNAMI_INSTANCE_NAME} -n ${DATA_E2E_POSTGRESML_NS}

# Undeploy PVC
kubectl delete -f resources/db/postgresml-cluster-pvc.yaml -n ${DATA_E2E_POSTGRESML_NS}

# Delete namespace
kubectl delete ns ${DATA_E2E_POSTGRESML_NS}