import logging
import traceback
import greenplumpython
from dotenv import load_dotenv
import os
import mlflow
import json

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

load_dotenv()


def run_task(prompt: str,
             task: str,
             model_name: str,
             experiment_name: str,
             use_topk: bool = 'y',
             inference_function_name: str = 'run_llm_inference_task'):
    """
    Runs a HuggingFace inference pipeline.
    :param prompt: Prompt text to be submitted to the transformers pipeline
    :param task: Pipeline task to be implemented
    :param model_name: Name of HuggingFace model
    :param experiment_name: Mlflow experiment to associate with this task
    :param use_topk: Flag indicating whether or not to use top-k semantic search to filter content
    :param inference_function_name: Name of inference function to invoke
    :return:
    """
    try:

        logger.info(f"Running: prompt={prompt}, model={model_name}, use_topk={use_topk}...")
        ####################
        # Store to database
        ###################

        # GreenplumPython
        db = greenplumpython.database(uri=os.getenv('DATA_E2E_LLMAPP_TRAINING_DB_URI'))

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

        ########################################
        # Track prompts
        ########################################
        track_prompts(model_name,
                      [prompt],
                      [json.dumps(answer)])

        return url, answer

    except Exception as ee:
        logger.info("An Exception occurred...", exc_info=True)
        logger.info(str(ee))
        logger.info(''.join(traceback.TracebackException.from_exception(ee).format()))


def track_prompts(model_name, inputs, outputs):
    with mlflow.start_run():
        try:
            experiment_name = 'llm_inference_tracking'
            mlflow.get_experiment_by_name(experiment_name) or mlflow.create_experiment(
                experiment_name,
            )
            os.environ['MLFLOW_EXPERIMENT_NAME'] = experiment_name
            mlflow.log_table(data={"model": model_name, "inputs": inputs, "outputs": outputs}, artifact_file="prompt_tracking.json")
        except Exception as ee:
            logger.info("An Exception occurred...", exc_info=True)
            logger.info(str(ee))
            logger.info(''.join(traceback.TracebackException.from_exception(ee).format()))

