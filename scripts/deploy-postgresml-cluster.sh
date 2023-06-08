source .env

# Deploy PVC
kubectl apply -f resources/db/postgresml-cluster-pvc.yaml \
      -n ${DATA_E2E_POSTGRESML_NS}

# Install Postgres instance
helm install postgresml-bitnami \
      oci://registry-1.docker.io/bitnamicharts/postgresql \
      -f resources/db/postgresml-cluster-values.yaml \
      -n ${DATA_E2E_POSTGRESML_NS}