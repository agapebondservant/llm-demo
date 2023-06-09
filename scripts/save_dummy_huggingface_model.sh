#!/usr/bin/env python3

from transformers import TFDistilBertForQuestionAnswering

from dotenv import load_dotenv

load_dotenv()

import sys

import os

repo_name = sys.argv[1]

clone_url = (f"https://{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}:"
             f"{os.getenv('DATA_E2E_HUGGINGFACE_TOKEN')}@huggingface.co/"
             f"{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}/{repo_name}")

os.system(f"git clone {clone_url}; cd {repo_name}")

model_name = f"{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}/{repo_name}"

print(f"=====================\nSaving model {model_name}...\n=====================\n")

model = TFDistilBertForQuestionAnswering.from_pretrained('distilbert-base-cased-distilled-squad')

model.save_pretrained('distilbert-base-cased-distilled-squad')

os.system("git add .; git commit -m 'Uploaded pretrained model'; git push; cd -; rm -rf {repo_name}")



