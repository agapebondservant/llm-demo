source .env

# Uninstall Postgres instance
helm uninstall postgresml-bitnami -n ${MY_POSTGRES_NS}

# Undeploy PVC
kubectl delete -f resources/db/postgresml-cluster-pvc.yaml -n ${MY_POSTGRES_NS}

# Delete namespace
kubectl delete ns ${MY_POSTGRES_NS}