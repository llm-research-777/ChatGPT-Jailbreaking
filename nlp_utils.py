
import spacy
import random
from api_utils import *
from helper_utils import *

def separateSentence(sentencce):
    """
    Create and return a spacy Doc object (with all nlp tag details) for a given sentence.

    Args:
        sentence (str): input sentence

    Returns:
        spacyDoc: spacy doc object with all nlp taggging details
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(sentencce)
    return doc

def translateSubSentence(doc, row, language_codes, lang = []):
    """
    Randomly translate selected parts(sub-sentence) of base question to a specified or random langauge.
    
    Args:
        doc (spacy Doc): converted doc object using  "en_core_web_sm"
        row (List): list is a row of output excel, this function adds more columns and returns the list.
        language_codes (list): valid google cloud translate langauge codes (for exception handling)
        lang (list, optional):  [language_code, language]. this is the language to which selected parts of base question will be translated to. 
        Defaults to [] each selected part of the base sentence will be transalted to different randomly choosen language. 
    """
    subject, verb, object = clearCashforSubSentence("", "", "")
    subLang, verbLang, objectLang = clearCashforSubSentence("", "", "")
    subFullLang, verbFullLang, objectFullLang = clearCashforSubSentence("", "", "")
    if lang:
        
        subTrans, verbTrans, objTrans = getTranSubSentenceFlageSingle() 
        if subTrans:
            subLang = lang[0]
            subFullLang = lang[1]
        else:
            subTrans = False
            
        if verbTrans:
            verbLang = lang[0]
            verbFullLang = lang[1]
        else:
            verbTrans = False
            
        if objTrans:  
            objectLang = lang[0]
            objectFullLang = lang[1]
        else:
            objTrans = False
            
    else:
        subTrans, verbTrans, objTrans = getTranSubSentenceFlage()  ## Which part should be translated

    flag = True  # A indictaor to print subject
    translation = ""
    for token in doc:
        if token.pos_ == "PUNCT":
            subLang, subFullLang2, subTranslation = translateSpecificPart(subTrans, subject, subLang, language_codes)
            if subFullLang2 == "": subFullLang2 = subFullLang
            verbLang, verbFullLang2, verbTranslation = translateSpecificPart(verbTrans, verb, verbLang, language_codes)
            if verbFullLang2 == "": verbFullLang2 = verbFullLang
            object = object[:-1] + token.text  ## Remove the last space
            objectLang, objectFullLang2, objTranslation = translateSpecificPart(objTrans, object, objectLang, language_codes)
            if objectFullLang2 == "": objectFullLang2 = objectFullLang

            # Update metadata
            translation += subTranslation
            translation += verbTranslation
            translation += objTranslation
            clearCashforSubSentence(subject, verb, object)
            flag = True
            continue
        
        #logic supports for the base queestion schema of the research
        if token.pos_ == "VERB":
            verb += token.text + " "
            flag = False #stop looking for subject once a verb is found
            continue
        if flag:
            subject += token.text + " "
        else:
            object += token.text + " "  ## if nor verb and after verb, At least one object

    part_trans_flag = "_".join([str(subTrans), str(verbTrans), str(objTrans)])
    #### Save the information for printing
    row += [part_trans_flag, subFullLang2, subLang, subject, verbFullLang2, verbLang, verb, objectFullLang2, objectLang, object,  translation]


# assumens input is english
def translateSpecificPart(shouldTranslate, part, chosenLanguage, language_codes, useCloudTranslate=True):
    """
    Translate a given part to specific target language, if choosenLanguage is "" random tatget language is choosen.
    
    Args:
        shouldTranslate (int): 1: tranlate, 0: dont translate
        part (str): string to be translated
        chosenLanguage (str): language code of target translation language, if empty string "" : random language is choosen.
        language_codes (list): valid google cloud translate langauge codes (for exception handling)
        use_cloud_translate (bool, optional): True uses google cloud translate else googletrans. Defaults to True.

    Returns:
        _type_: _description_
    """
    translation = ""
    targetLang = [""]
    if shouldTranslate:
        if chosenLanguage == "":  ## if language is not specified
            targetLang = chooseTargetLanguage()
            chosenLanguage = targetLang[1][:-1]
        if useCloudTranslate:
            translation += cloudTranslate(chosenLanguage, part, language_codes) + " "
        else:
            translation += translate(chosenLanguage, part) + " "
    else:
        chosenLanguage = "en"
        targetLang[0] = "english"
        translation += part  ## print the original input
    return chosenLanguage, targetLang[0], translation

def clearCashforSubSentence(subject, verb, object):
    """
    helper util function for clearing cache

    Args:
        subject (str): previous sentence subject 
        verb (str): previous sentence verb 
        object (str): previous sentence object 

    Returns:
        tuple: ("","","")
    """
    subject = ""
    verb = ""
    object = ""
    return subject, verb, object
    
def getTranSubSentenceFlageSingle():
    """
    Randomly choose only "one" of 3 parts (used for part wise language conversion tasks)
    Returns: three values for subject, verb and object respectively (1 indicates selected and 0 indicates not selected) 

    Returns:
        tuple: (binary_int, binary_int, binary_int). only one of them will be 1
    """
    type = random.choice([1,2,4]) # only 001 , 010, 100  Subject, Verb, Object
    subTrans = ((type // 4) == 1)
    verbTrans = (((type % 4) // 2) == 1)
    objTrans = ((type % 2) == 1)
    return subTrans, verbTrans, objTrans

def getTranSubSentenceFlage():
    """_
    Randomly choose "any number of" 3 parts (used for part wise language conversion tasks)
    Returns: three values for subject, verb and object respectively (1 indicates selected and 0 indicates not selected) 
    
    Returns:
        tuple: (binary_int, binary_int, binary_int). 
    """
    type = random.randint(1,7)  # 001 -- 111  Subject, Verb, Object
    subTrans = ((type // 4) == 1)
    verbTrans = (((type % 4) // 2) == 1)
    objTrans = ((type % 2) == 1)
    return subTrans, verbTrans, objTrans