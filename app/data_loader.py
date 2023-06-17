import logging
import mlflow
import traceback
import greenplumpython
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

load_dotenv()


def store_tokens(url_path: str, text: str, experiment_name: str, chunk_size: int = 100, chunk_overlap: int = 5):
    """
    Logs tokens to the MLflow artifact store.
    :param text: Text to be converted and stored as chunks
    :param url_path: URL to the pdf file associated with the text
    :param experiment_name: Mlflow experiment to associate with this task
    :param chunk_overlap: Number of overlapping tokens to use for splits
    :param chunk_size: Number of tokens per pdf chunk to use for splits
    :return:
    """
    try:

        logger.info(f"Storing data for {url_path}...")
        ####################
        # Store to database
        ###################

        # GreenplumPython
        db = greenplumpython.database(uri=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))
        logger.info(os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))
        loader_function_name = 'run_loader_task'
        loader_function = greenplumpython.function(loader_function_name,
                                                   schema=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_SCHEMA'))

        # TODO: Find a different way to handle Unicode characters - GreenplumPython currently supports ASCII,
        #  so the encoding below will result in data loss of unicode chars
        url_ascii, text_ascii = url_path.encode('ascii', 'replace').decode(), text.encode('ascii', 'replace').decode()

        df = db.apply(lambda: loader_function(url_ascii, text_ascii, f"{chunk_size}", f"{chunk_overlap}"))
        num_tokens = next(iter(df))[loader_function_name]
        logger.info(f"Number of tokens saved for {url_path} = {num_tokens}")

        ####################
        # Log token in Mlflow
        ####################
        with mlflow.start_run():
            mlflow.get_experiment_by_name(experiment_name) or mlflow.create_experiment(
                experiment_name,
                artifact_location="pdfs",
            )
            os.environ['MLFLOW_EXPERIMENT_NAME'] = experiment_name
            mlflow.set_tags({"embeddable_docs": "y"})
            mlflow.log_text(url_path, f"{num_tokens}")

    except Exception as ee:
        logger.info("An Exception occurred...", exc_info=True)
        logger.info(str(ee))
        logger.info(''.join(traceback.TracebackException.from_exception(ee).format()))
