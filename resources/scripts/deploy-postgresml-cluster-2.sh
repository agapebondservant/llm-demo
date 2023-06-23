source .env

# Create namespace
kubectl create ns ${MY_POSTGRES_NS}

# Deploy PVC
kubectl apply -f resources/db/postgresml-cluster-pvc.yaml \
      -n ${MY_POSTGRES_NS}

# Install Postgres instance
envsubst < resources/db/postgresml-cluster-values.yaml | helm install postgresml-bitnami \
      oci://registry-1.docker.io/bitnamicharts/postgresql \
      -n ${MY_POSTGRES_NS} \
      -f -