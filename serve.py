import re

from flask import Flask

from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

def extract_code(markdown_text):
    code_regex = r"```html\s+(.*?)\s+```"
    code_matches = re.findall(code_regex, markdown_text, re.DOTALL)
    if code_matches:
        return code_matches[0]
    else:
        return "Something went wrong parsing the regex."

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
        endpoint="projects/genai-coding/locations/us-central1/publishers/google/models/code-bison@001", 
        instances=instances, 
        parameters=parameters
    )
    predictions = response.predictions

    for prediction in predictions: return extract_code(prediction.get("content", ""))

app = Flask(__name__)

@app.route('/')
def index():
    return 'Usage: /company_name/product/core_value (use underscores as spaces) (generating might take 10s+.)'

@app.route('/<string:company_name>/<string:product>/<string:core_value>')
def generate_landingpage(company_name, product, core_value):
    company_name = company_name.replace('_', ' ')
    product = product.replace('_', ' ')
    core_value = core_value.replace('_', ' ')
    context = f"""Write a html landing page for a company called {company_name}. 
{company_name} is a {product} maker. {company_name}'s core value is {core_value}. 
Use bootstrap css to style the webpage. The page should have a navbar and a footer. 
The webpage should include a hero banner, pricing plans (in a table), the company mission statement, 
currently open roles and customer quotes of people using {product} with attention to {core_value}."""
    print("Context: ", context)
    return query_code_bison(context, temp=0.8)

if __name__ == '__main__':
    app.run(debug=True)