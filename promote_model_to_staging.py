from app.analytics import model_customization
import sys

# Publish the model to HuggingFace
model_customization.publish_model(repo_name=sys.argv[1], pretrained_model_name=sys.argv[2])

# Promote the model to Staging in the Model Registry
model_customization.promote_model_to_staging(model_name=f"{sys.argv[1]}", pipeline_name=sys.argv[7], persist_model_copy=sys.argv[8])

# Publish metadata to the data catalog
model_customization.send_metadata(model_name=f"{sys.argv[1]}", platform=sys.argv[3], env=sys.argv[4], gms_server=sys.argv[5], model_description=sys.argv[6])


