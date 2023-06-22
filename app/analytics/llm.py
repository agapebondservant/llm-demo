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


def run_task(prompt: str, task: str, model_name: str, experiment_name: str, use_topk: bool = 'y'):
    """
    Runs a HuggingFace inference pipeline.
    :param prompt: Prompt text to be submitted to the transformers pipeline
    :param task: Pipeline task to be implemented
    :param model_name: Name of HuggingFace model
    :param experiment_name: Mlflow experiment to associate with this task
    :param use_topk: Flag indicating whether or not to use top-k semantic search to filter content
    :return:
    """
    try:

        logger.info(f"Running: {prompt}...")
        ####################
        # Store to database
        ###################

        # GreenplumPython
        db = greenplumpython.database(uri=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))
        inference_function_name = 'run_llm_inference_task'

        ########################################
        # Invoke loader function
        ########################################
        inference_function = greenplumpython.function(inference_function_name,
                                                      schema=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_SCHEMA'))

        df = db.apply(lambda: inference_function(prompt, task, model_name, use_topk))
        result = next(iter(df))[inference_function_name]
        logger.info(f"{result} {type(result)}")
        url, answer = result["doc_url"], result["result"]
        logger.info(f"Results:\nurl={url}\nresult={answer} ({type(answer)})")

        ####################
        # Log token in Mlflow
        ####################
        """
        with mlflow.start_run():
            mlflow.get_experiment_by_name(experiment_name) or mlflow.create_experiment(
                experiment_name,
                artifact_location="pdfs",
            )
            os.environ['MLFLOW_EXPERIMENT_NAME'] = experiment_name
            mlflow.set_tags({"embeddable_docs": "y"})
            mlflow.log_dict({url_path: num_tokens}, 'data')
        """
        return url, answer

    except Exception as ee:
        logger.info("An Exception occurred...", exc_info=True)
        logger.info(str(ee))
        logger.info(''.join(traceback.TracebackException.from_exception(ee).format()))
