import re, logging
import vertexai

from functools import lru_cache

from flask import Flask
from dotenv import dotenv_values
from vertexai.preview.language_models import CodeGenerationModel


logging.basicConfig(level=logging.INFO)

cfg = dotenv_values('.env')
vertexai.init(project=cfg['PROJECT_ID'], location="us-central1")
model = CodeGenerationModel.from_pretrained("code-bison@001")

def extract_code(markdown_text):
    logging.info("markdown_text: " + markdown_text)
    if len(markdown_text) == 0: 
        logging.warning("markdown_text is empty.")
        return None
    code_regex = r"```(?:html)?(.*)(?:```)?"
    code_matches = re.findall(code_regex, markdown_text, re.DOTALL)
    if len(code_matches) != 1:
        logging.warning("regex code_matches is not 1.")
        logging.info('markdown_text: ', markdown_text)
        return None
    else:
        return code_matches[0]

@lru_cache(maxsize=128)
def query_code_bison(ctx, temp=0.5, max_tokens=2048):

    parameters = {
        "temperature": temp,
        "max_output_tokens": max_tokens,
    }
    response = model.predict(
        prefix = ctx,
        **parameters
    )
    # TODO: check and handle ['safetyAttributes']['blocked'] when implemented
    if len(response.text) == 0:
        raise Exception("Empty response from vertexai")

    res = extract_code(response.text)
    if res == None:
        # Raising exception without returning avoid caching bad response
        raise Exception("Regex parsing error.")

    return res


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
    logging.info('context: ' + context)
    try:
        res = query_code_bison(context, temp=0.8, max_tokens=2048) 
        logging.info(query_code_bison.cache_info())
        return res
    except Exception as e:
        logging.error(e)
        if e.args[0] == "Empty response from vertexai":
            return "Error (likely safety filter). Try again a few times. You can also try changing the parameters."
        return "Error: " + str(e)

if __name__ == '__main__':
    app.run(debug=True)