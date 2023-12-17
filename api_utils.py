
from googletrans import Translator
from google.cloud import translate
import google.generativeai as palm
from datetime import datetime
import openai

#Open AI config
openai.api_key = "<Your API key Here>"

#PALM config
# palm.configure(api_key="")
# palm_models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
# palm_model = palm_models[0].name

#Google Cloud cofig (for cloudtranslation api)
PARENT = f"projects/<Your google cloud project>"
client = translate.TranslationServiceClient()


def get_supported_languages(display_language_code: str):
    """
    Conencts to the google cloud translation service and get supported languuages from cloud

    Args:
        display_language_code (str): api output langauage for reading the information asked
    Returns:
        list: list of langauge objects
    """
    response = client.get_supported_languages(
        parent=PARENT,
        display_language_code=display_language_code,
    )
    return response.languages

def translate(toLang, content):
    """
    googletrans package based translation
    Translates the content passes to the language specified using googletrans api

    Args:
        toLang (str): language code of the target language
        content (str): string to be translated

    Returns:
        str: translated string
    """
    
    translator = Translator()
    translation = translator.translate(content, dest=toLang)
    return translation.text

def cloudTranslate(toLang, content, language_codes):
    """
    Google Cloud based translation
    Translates the content passes to the language specified using google cloud tranlation api

    Args:
        toLang (str): language code of the target language
        content (str): string to be translated
        language_codes (list): valid google cloud translate langauge codes (for exception handling)

    Returns:
        str: translated string
    """
    try:
        if toLang in language_codes:
            response = client.translate_text(
                parent=PARENT,
                contents=[content],
                target_language_code=toLang,
                mime_type = "text/plain"
            )
            return response.translations[0].translated_text
        else:
            return "ERR: LANGUAGE CODE INVALID"
    except Exception as e:
        # logger.error("ERR: " + str(e))
        return "ERR: GCLOUD TRANSLATION NOT COMPLETE, Check Logs " + datetime.now().isoformat()
    

def chatgpt_response(content):
    """
    response one time response to the question from GPT chat api, with no chat history
    model used: "gpt-3.5-turbo"

    Args:
        content (str): Prompt to GPT chat

    Returns:
        str: GPT Chat Response
    """
    try:
        chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": content }], request_timeout=180
            )
        if chat.choices[0].finish_reason == "stop":
            return chat.choices[0].message.content
        else:
            return "ERR: TRANSLATION NOT COMPLETED"
    except Exception as e:
        # logger.error("ERR: " + str(e))
        return "ERR: GPT TRANSLATION NOT COMPLETE, Check Logs " + datetime.now().isoformat()  
    
def palm_response(content):
    """
    response one time response to the question from PALM chat api, with no chat history
    model used: "PALM2"

    Args:
        content (str): Prompt to PALM chat

    Returns:
        str: PALM Chat Response
    """
    try:
        model = ""
        completion = palm.generate_text(
                            model=model,
                            prompt=content,
                            temperature=0,
                            # The maximum length of the response
                            max_output_tokens=800,
                            )
        
        if completion.result == None:
            if completion.filters:
               return str(completion.filters[0]["reason"]) #blocked the response through filters
            else:
               return "unknown error" #any other error
        else:
            return completion.result #general response
    except Exception as e:
        return str(e) #other errors like language not supported