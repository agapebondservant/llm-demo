#!/usr/bin/env python3

from transformers import DistilBertTokenizer, TFDistilBertForQuestionAnswering

from dotenv import load_dotenv

load_dotenv()

import sys

import os

repo_name = sys.argv[1]

clone_url = (f"https://{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}:"
             f"{os.getenv('DATA_E2E_HUGGINGFACE_TOKEN')}@huggingface.co/"
             f"{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}/{repo_name}")

os.system(f"git clone {clone_url}; cd {repo_name}; git lfs install; huggingface-cli lfs-enable-largefiles .")

model_name = f"{os.getenv('DATA_E2E_HUGGINGFACE_USERNAME')}/{repo_name}"

print(f"=====================\nSaving model {model_name}...\n=====================\n")

model = DistilBertTokenizer.from_pretrained("distilbert-base-cased-distilled-squad")
tokenizer = TFDistilBertForQuestionAnswering.from_pretrained("distilbert-base-cased-distilled-squad")

model.save_pretrained("distilbert-base-cased-distilled-squad")

tokenizer.save_pretrained("distilbert-base-cased-distilled-squad")

os.system(f"cd {repo_name}; mv ../distilbert-base-cased-distilled-squad/* .;"
          "rm -rf ../distilbert-base-cased-distilled-squad; git add .;"
          "git commit -m 'Uploaded pretrained model';"
          f"git push; cd -; rm -rf {repo_name}")


