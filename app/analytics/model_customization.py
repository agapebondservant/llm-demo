import datahub.emitter.mce_builder as builder
import datahub.metadata.schema_classes as models
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from huggingface_hub import ModelCard
from transformers import DistilBertTokenizer, TFDistilBertForQuestionAnswering
from dotenv import load_dotenv
import os
import mlflow
from mlflow import MlflowClient
from transformers import pipeline

load_dotenv()


def send_metadata(model_name: str,
                  platform: str,
                  env: str,
                  gms_server: str,
                  model_description: str = None):
    with mlflow.start_run(run_name='send_metadata', nested=True):
        emitter = DatahubRestEmitter(gms_server=gms_server, extra_headers={})
        model_urn = builder.make_ml_model_urn(
            model_name=model_name, platform=platform, env=env
        )
        model_card = ingest_metadata_from_huggingface_model(model_name)

        metadata_change_proposal = MetadataChangeProposalWrapper(
            entityType="mlModel",
            changeType=models.ChangeTypeClass.UPSERT,
            entityUrn=model_urn,
            aspectName="mlModelProperties",
            aspect=models.MLModelPropertiesClass(
                description=model_card.text,
                customProperties={**{k: ','.join(v) for (k, v) in model_card.data.to_dict().items()},
                                  **{'Last Updated': ''}})
    )

    emitter.emit(metadata_change_proposal)


def ingest_metadata_from_huggingface_model(model_name: str):
    card = ModelCard.load(model_name)
    return card or {}


def publish_model(repo_name: str, pretrained_model_name: str):
    with mlflow.start_run(run_name='publish_model', nested=True):
        # TODO: DO NOT HARDCODE!!!
        clone_url = (f"https://tanzuhuggingface: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@huggingface.co/"
                     f"tanzuhuggingface/{repo_name}")

        model_name = f"tanzuhuggingface/{repo_name}"

        print(f"=====================\nSaving model {model_name}...\n=====================\n")

        model = DistilBertTokenizer.from_pretrained(pretrained_model_name)
        tokenizer = TFDistilBertForQuestionAnswering.from_pretrained(pretrained_model_name)
        model.save_pretrained(pretrained_model_name)
        tokenizer.save_pretrained(pretrained_model_name)

        os.system(f"git clone {clone_url}; "
                  f"cd {repo_name};"
                  "git config --global user.email 'tanzuhuggingface@example.com';"
                  "git config --global user.name 'Tanzu Huggingface';"
                  f" git lfs install; "
                  f"huggingface-cli lfs-enable-largefiles .;"
                  f"mv ../{pretrained_model_name}/* .;"
                  f"rm -rf ../{pretrained_model_name}; "
                  "git add .;"
                  "git commit -m 'Uploaded pretrained model';"
                  f"git push; "
                  f"cd -; rm -rf {repo_name}")


def promote_model_to_staging(model_name, pipeline_name):
    client = MlflowClient(model_name)

    # TODO: Determine correct version
    with mlflow.start_run(run_name='promote_model_to_staging', nested=True):
        client.transition_model_version_stage(
            name=model_name,
            version=1,
            stage="Staging"
        )

    qa_pipe = pipeline(pipeline_name, model_name)
    mlflow.transformers.log_model(
        transformers_model=qa_pipe,
        artifact_path=pipeline_name,
    )

