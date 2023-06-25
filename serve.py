import os, re, logging
import vertexai

from functools import lru_cache

from flask import Flask, render_template, request
from dotenv import load_dotenv
from vertexai.preview.language_models import CodeGenerationModel


logging.basicConfig(level=logging.INFO)
load_dotenv()

vertexai.init(project=os.getenv('PROJECT_ID'), location="us-central1")
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
    return render_template('./index.html')
    
@app.route('/generate')
def generate_landingpage():
    company_name = request.args.get('company_name')
    product = request.args.get('product')
    core_value = request.args.get('core_value')
    context = open('prompts/design_landingpage').read().format(**locals())
    logging.info('context: ' + context)
    try:
        res = query_code_bison(context, temp=0.5, max_tokens=2048) 
        logging.info(query_code_bison.cache_info())
        info_banner = """what is this? >> <a target="_blank" href="https://github.com/antonpp/wdiia">github.com/antonpp/wdiia</a> <br/>""" 
        return info_banner + res
    except Exception as e:
        logging.error(e)
        if e.args[0] == "Empty response from vertexai":
            return "Error (likely safety filter). Try again a few times. You can also try changing the parameters."
        return "Error: " + str(e)

if __name__ == '__main__':
    app.run(debug=True)