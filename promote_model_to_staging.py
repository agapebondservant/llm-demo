from app.analytics import model_customization
import sys

model_customization.publish_model(repo_name=sys.argv[1], pretrained_model_name=sys.argv[2])

model_customization.promote_model_to_staging(model_name=f"tanzuhuggingface/{sys.argv[1]}", pipeline_name=sys.argv[7], persist_model_copy=sys.argv[8])

model_customization.send_metadata(model_name=f"tanzuhuggingface/{sys.argv[1]}", platform=sys.argv[3], env=sys.argv[4], gms_server=sys.argv[5], model_description=sys.argv[6])


