import datahub.emitter.mce_builder as builder
import datahub.metadata.schema_classes as models
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from huggingface_hub import ModelCard


def send_metadata(model_name: str,
                  platform: str,
                  env: str,
                  gms_server: str,
                  model_description: str = None):
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
