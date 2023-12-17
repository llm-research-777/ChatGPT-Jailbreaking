import linecache
import random

def chooseInput():
    """
    Randomly choose a record (english question) from input file containing base set of questions

    Returns:
        str: choosen base english question.
    """
    recordIndex = random.randint(1, 30)
    record = linecache.getline('./data/base/input.csv', recordIndex)
    return record

def chooseTargetLanguage():
    """
    Randomly select a language and its code from the base languages file

    Returns:
        list: [<language>, <lang_code>]
    """
    recordIndex = random.randint(1, 105)  ## The supported language file doesn't include "english"
    row = linecache.getline('./data/base/language.csv', recordIndex).split(",")
    return row