from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
import mlflow
import traceback
import greenplumpython
from dotenv import load_dotenv
import os
from transformers import pipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

load_dotenv()


def store_tokens(file_path: str, text: str, experiment_name: str):
    """
    Logs tokens to the MLflow artifact store.
    :param text: Text to be converted and stored as chunks
    :param file_path: path to the pdf file associated with the text
    :param experiment_name: Mlflow experiment to associate with this task
    :return:
    """
    try:
        tokens = extract_chunks_from_text(text)

        logger.info(f"Storing tokens for {file_path}...")
        for idx, token in enumerate(tokens):
            ####################
            # Store to database
            ###################

            # GreenplumPython
            db = greenplumpython.database(uri=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))
            logger.info(os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))
            loader_function_name = 'run_loader_task'
            loader_function = greenplumpython.function(loader_function_name,
                                                       schema=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_SCHEMA'))
            df = db.apply(lambda: loader_function(file_path, token))
            # status = next(iter(df))[loader_function_name]
            logger.info(f"Database update status for {file_path}, token {idx}= {df}")

            ####################
            # Log token in Mlflow
            ###################
            mlflow.get_experiment_by_name(experiment_name) or mlflow.create_experiment(
                experiment_name,
                artifact_location="pdfs",
            )
            os.environ['MLFLOW_EXPERIMENT_NAME'] = experiment_name

        with mlflow.start_run():
            mlflow.set_tags({"embeddable_docs": "y"})
            mlflow.log_text(file_path, f"{idx}")

            """    qa_pipe = pipeline("question-answering", "distilbert-base-cased-distilled-squad")
                mlflow.transformers.log_model(
                    transformers_model=qa_pipe,
                    artifact_path="test_pipeline_qa",
                )"""

    except Exception as ee:
        logger.info("An Exception occurred...", exc_info=True)
        logger.info(str(ee))
        logger.info(''.join(traceback.TracebackException.from_exception(ee).format()))


def extract_chunks_from_text(text: str, chunk_size: int = 100, chunk_overlap: int = 5):
    """
    Extracts BPE-compressed chunks from the given text.
    :param chunk_overlap: Number of overlapping tokens to use for splits
    :param chunk_size: Number of tokens per pdf chunk to use for splits
    :param text: Text to be chunked
    :return: Binary Pair Encoded chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    tokens = text_splitter.split_text(text)
    return tokens
