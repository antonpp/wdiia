import re
import os
import logging

from flask import Flask
from dotenv import dotenv_values

from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

cfg = dotenv_values('.env')

def extract_code(markdown_text):
    if len(markdown_text) == 0: 
        return "Something went wrong with the request."
    code_regex = r"```(?:html)?(.*?)```"
    code_matches = re.findall(code_regex, markdown_text, re.DOTALL)
    if code_matches:
        return code_matches[0]
    else:
        logging.info("Empty list of matches for code_regex.")
        logging.info('markdown_text: ', markdown_text)
        return "Something went wrong parsing the reply."

def query_code_bison(ctx, temp=0.5, max_tokens=2048):
    client_options = {"api_endpoint": "us-central1-aiplatform.googleapis.com"}

    client = aiplatform.gapic.PredictionServiceClient(
        client_options=client_options
    )
    instance_dict = {
        "prefix": ctx
    }
    instance = json_format.ParseDict(instance_dict, Value())
    instances = [instance]
    parameters_dict = {
        "temperature": temp,
        "maxOutputTokens": max_tokens,
    }
    parameters = json_format.ParseDict(parameters_dict, Value())
    response = client.predict(
        endpoint=f"projects/{cfg['PROJECT_ID']}/locations/us-central1/publishers/google/models/code-bison@001", 
        instances=instances, 
        parameters=parameters
    )
    predictions = response.predictions

    for prediction in predictions: 
        if prediction.get("safetyAttributes")['blocked']:
            logging.info("safetyAttributes blocked")
            return "Something went wrong with content of the request or reply. (try refreshing or changing the input)"
        return extract_code(prediction.get("content"))

app = Flask(__name__)

@app.route('/')
def index():
    return 'Usage: /company_name/product/core_value (use underscores as spaces) (generating might take 10s+.)'

@app.route('/<string:company_name>/<string:product>/<string:core_value>')
def generate_landingpage(company_name, product, core_value):
    company_name = company_name.replace('_', ' ')
    product = product.replace('_', ' ')
    core_value = core_value.replace('_', ' ')
    context = open('prompts/design_landingpage').read().format(**locals())
    logging.info('context: ', context)
    return query_code_bison(context, temp=0.8)

if __name__ == '__main__':
    app.run(debug=True)