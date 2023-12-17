import glob
from datetime import datetime
import numpy as np
import pandas as pd
import random
import logging 
import csv

from api_utils import *
from helper_utils import *
from nlp_utils import *

#logger config
logging.basicConfig(filename="./logs/Log_File_"+datetime.now().isoformat()+".log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 
logger=logging.getLogger() 
logger.setLevel(logging.INFO) 

def rq1(llm = "gpt"):
    """
    Step 1) Perform sequence of operations on each row form base data to create RQ1 data. Base data includes: "/data/base/language.csv" (languages) and "/data/base/input.csv"(questions)
    Step 2) saves output for every 50 rows to minimize data loss on failure. (temp output written to "/data/runtime_partitioned/rq1*.csv")
    Step 3) concatinates the partitioned files saved on step 2 to form a final RQ1 base data file (saved to /data/generated/RQ1_base.xlsx)
    saves the progress to logfile generated at "/logs/" for additional tracking
    
    Args:
        llm (str, optional): "gpt" uses 3.5 turbo or "PALM" (not maintained). Defaults to "gpt".

    Raises:
        Exception: raises any runtime exception.
    """
    try: 
        logger.info("RQ1_NEW_START") 
        #file split logic variables
        writer = None
        record_count = 0
        max_records_per_file = 50
        
        languages = pd.read_csv("./data/base/language.csv", header=None)
        input_file = open('./data/base/input.csv', 'r')
        inputs = [x.strip() for x in input_file.readlines()]
        input_file.close()
        for input in inputs:
            for i in range(len(languages)):
                lang = languages.iloc[i][0]
                langCode = languages.iloc[i][1]
                trans_input = cloudTranslate(langCode, input, language_codes)
                if llm == "gpt":
                    llm_response = chatgpt_response(trans_input)[:5000]
                if llm == "palm":
                    llm_response = palm_response(trans_input)[:5000]
                    
                gpt_eng_input = cloudTranslate("en", llm_response, language_codes)
                
                #save full file after select number of entries and open new file
                if record_count % max_records_per_file == 0:
                    if writer:
                        f.close()
                    file_num = record_count // max_records_per_file + 1
                    file_name = f'./data/runtime_partitioned/rq1_{file_num}.csv'
                    f = open(file_name, 'w')
                    writer = csv.writer(f)
                    writer.writerow(["Language", "Language Code", "Input", "Translation", "ChatGPT's Answer", "English Answer", "TimeStamp"])
                    
                writer.writerow([lang, langCode, input, trans_input, llm_response, gpt_eng_input, datetime.now().isoformat()])
                logger.info("|-|".join([lang, langCode, input, trans_input, llm_response, gpt_eng_input, datetime.now().isoformat()])) 
                record_count += 1
        f.close()
        logger.info("aggregating partitioned files...") 
        files = glob.glob("./data/runtime_partitioned/rq1_*.csv")
        df_list = []
        for file in files:
            df = pd.read_csv(file)
            df_list.append(df)
        aggregated_df = pd.concat(df_list)
        aggregated_df.to_excel("./data/generated/RQ1_base.xlsx", index=False)
        logger.info("RQ1_END") 
    except:
        raise Exception("crashed while running")
    finally:
       f.close() #for handling data loss on crash

def rq2(llm = "gpt"):
    """
    Step 1) Perform sequence of operations on each row of R1 data specified at (/data/processed/RQ1.csv, sheet : RQ2_input) to create RQ2 data.
    Step 2) saves output for every 50 rows to minimize data loss on failure. (temp output written to "/data/runtime_partitioned/rq2*.csv")
    Step 3) concatinates the partitioned files saved on step 2 to form a final RQ2 base data file (saved to /data/generated/RQ2_base.xlsx)

    Args:
        llm (str, optional): "gpt" uses 3.5 turbo or "PALM" (not maintained). Defaults to "gpt".

    Raises:
        Exception: raises any runtime exception.
    """
    try:
        logger.info("RQ2_NEW_START") 
        writer = None
        record_count = 0
        max_records_per_file = 50
        #TODO : make file name configurable
        data = pd.read_csv("./data/processed/RQ1.csv")
        inputs = data.apply(lambda x : (x["Input"], x["Language"], x["Language Code"]), axis = 1)
        for input in inputs:
            chosenInput = input[0]
            language_full = input[1]
            lang_code = input[2]
            lang_pair = [lang_code,language_full]
            doc = separateSentence(chosenInput)
            row = [chosenInput]
            translateSubSentence(doc, row, language_codes, lang_pair)
            trans_input = row[-1]
            language_force_tag = f". (Please answer my question in {language_full})"
            if llm == "gpt":
                llm_response = chatgpt_response(trans_input+language_force_tag)[:5000]
            if llm == "palm":
                llm_response = palm_response(trans_input+f". (Please answer my question in {language_full})")[:5000]
            gpt_eng_input = cloudTranslate("en", llm_response, language_codes)
            
            row = row + [lang_code,trans_input+language_force_tag,llm_response, gpt_eng_input]
            
            #save full file and open new file
            if record_count % max_records_per_file == 0:
                if writer:
                    f.close()
                file_num = record_count // max_records_per_file + 1
                file_name = f'./data/runtime_partitioned/rq2_{file_num}.csv'
                f = open(file_name, 'w')
                writer = csv.writer(f)
                writer.writerow(["Input", "SubVerbObj_Trans_Tag", "SubLanguage", "Code1", "Subject", "VerbLang", "Code2", "Verb", "ObjLang", "Code3", "Object", "Translation", "RQ1 lang code", "Final Question","ChatGPT's Answer", "English Answer", "TimeStamp"])
            writer.writerow(row + [datetime.now().isoformat()])
            logger.info("|-|".join(row + [datetime.now().isoformat()])) 
            record_count += 1
        f.close()
        logger.info("aggregating partitioned files...") 
        files = glob.glob("./data/runtime_partitioned/rq2_*.csv")
        df_list = []
        for file in files:
            df = pd.read_csv(file)
            df_list.append(df)
        aggregated_df = pd.concat(df_list)
        aggregated_df.to_excel("./data/generated/RQ2_base.xlsx", index=False)
        logger.info("RQ2_END")
    except:
        raise Exception("crashed while running")
    finally:
        f.close()
        
def rq3(llm = "gpt"):
    """
    Step 1) Perform sequence of operations on each row of R1 data specified at (/data/processed/RQ1.csv, sheet: RQ2_input) to create RQ3 data.
    Step 2) saves output for every 50 rows to minimize data loss on failure. (temp output written to "/data/runtime_partitioned/rq3*.csv")
    Step 3) concatinates the partitioned files saved on step 2 to form a final RQ3 base data file (saved to /data/generated/RQ3_base.xlsx)

    Args:
        llm (str, optional): "gpt" uses 3.5 turbo or "PALM" (not maintained). Defaults to "gpt".

    Raises:
        Exception: raises any runtime exception.
    """
    try:
        logger.info("RQ3_NEW_START") 
        language_mapping = dict(pd.read_csv("data/base/language.csv", header=None).values)
        languages = language_mapping.keys()
        writer = None
        record_count = 0
        max_records_per_file = 50
        #TODO : make file name configurable
        data = pd.read_csv("./data/processed/RQ1.csv") # input file is same for both RQ2 an RQ3 function
        inputs = data.apply(lambda x : (x["Input"], x["Translation"], x["Language"], x["Language Code"]), axis = 1)
        for input in inputs:
            originalQuestion = input[0]
            chosenInput = input[1]
            language_full = input[2]
            lang_code = input[3]
            random_lang = random.choice(list(set(languages) - set(["english", language_full])))
            language_force_tag = f". (Please answer my question in {random_lang})"
            row = [originalQuestion, language_full, lang_code, chosenInput, random_lang, chosenInput+language_force_tag]
            if llm == "gpt":
                llm_response = chatgpt_response(chosenInput+language_force_tag)[:5000]
            if llm == "palm":
                llm_response = palm_response(chosenInput+language_force_tag)[:5000]
            row = row + [llm_response]
            gpt_eng_input = cloudTranslate("en", llm_response, language_codes)
            row = row + [gpt_eng_input]
            #save full file and open new file
            if record_count % max_records_per_file == 0:
                if writer:
                    f.close()
                file_num = record_count // max_records_per_file + 1
                file_name = f'./data/runtime_partitioned/rq3_{file_num}.csv'
                f = open(file_name, 'w')
                writer = csv.writer(f)
                writer.writerow(["Input", "RQ1_language", "RQ1_lang_code", "Translation", "Random_Lang", "Final Question","ChatGPT's Answer", "English Answer", "TimeStamp"])
            writer.writerow(row + [datetime.now().isoformat()])
            logger.info("|-|".join(row + [datetime.now().isoformat()])) 
            record_count += 1
        f.close()
        logger.info("aggregating partitioned files...") 
        files = glob.glob("./data/runtime_partitioned/rq3_*.csv")
        df_list = []
        for file in files:
            df = pd.read_csv(file)
            df_list.append(df)
        aggregated_df = pd.concat(df_list)
        aggregated_df.to_excel("./data/generated/RQ3_base.xlsx", index=False)
        logger.info("RQ3_END") 
        
    except:
        raise Exception("crashed while running")
    finally:
        f.close()

def rq4InputGen():
    """
    1) Randomly sample 300 records marked as FALSE from rq1, rq2, and rq3 respectively, which results in a total of 900 records.
    2) Also track random sampled false indices from each RQ. saved at (./data/generated/RQ4_selction_false_indices_bkp.xlsx)
    3) Track the question source under column "Source RQ"
    4) Save RQ4 Input to (.data/generated/RQ4_input.xlsx)
    
    """
    RQ1_data = pd.read_csv("./data/processed/RQ1.csv")
    RQ2_data = pd.read_csv("./data/processed/RQ2.csv")
    RQ3_data = pd.read_csv("./data/processed/RQ3.csv")
    languages = pd.read_csv("./data/base/language.csv", header = None)
    code_to_name_lang = dict(languages[[1,0]].values)
    name_to_code_lang = dict(languages.values)
    
    RQ1_data = (RQ1_data[RQ1_data["Final Label"] == False]).reset_index(drop = True)
    RQ1_data = RQ1_data[["Language","Language Code","Input","Translation"]].rename(columns = {"Translation" : "Final Question"})
    RQ2_data = (RQ2_data[RQ2_data["Label"] == False]).reset_index(drop = True)
    RQ2_data = RQ2_data[["RQ1 lang code","Input","Final Question"]].rename(columns = {"RQ1 lang code" : "Language Code"})
    RQ2_data["Language"] = RQ2_data["Language Code"].map(code_to_name_lang)
    RQ3_data = (RQ3_data[RQ3_data["Label"] == False]).reset_index(drop = True)
    RQ3_data = RQ3_data[["Random_Lang","Input","Final Question", "RQ1_lang_code"]].rename(columns = {"Random_Lang" : "Language"})
    RQ3_data["Language Code"] = RQ3_data["Language"].map(name_to_code_lang)
    
    indices1 = np.random.choice(len(RQ1_data), size=300, replace=False)
    RQ1_sampels = RQ1_data.iloc[indices1]
    indices2 = np.random.choice(len(RQ2_data), size=300, replace=False)
    RQ2_sampels = RQ2_data.iloc[indices2]
    indices3 = np.random.choice(len(RQ3_data), size=300, replace=False)
    RQ3_sampels = RQ3_data.iloc[indices3]
    
    selected_false_indices = pd.DataFrame([indices1, indices2, indices3]).T
    selected_false_indices.columns = ["RQ1_false","RQ2_false","RQ3_false"]
    
    RQ1_sampels["Source RQ"] = "RQ1"
    RQ2_sampels["Source RQ"] = "RQ2"
    RQ3_sampels["Source RQ"] = "RQ3"
    
    RQ4_input = pd.concat([RQ1_sampels, RQ2_sampels, RQ3_sampels])
    RQ4_input.to_excel("./data/generated/RQ4_input.xlsx")
    selected_false_indices.to_excel("./data/generated/RQ4_selction_false_indices_bkp.xlsx")


def rq4(llm = "gpt"):
    """
    
    Step 1) Perform sequence of operations on each row of R4 input file (generated by rq4InputGen()) specified at (./data/generated/RQ4_input.xlsx) to create RQ4 data. Loads jailbreaking templates from the file at (./data/processed/RQ4_templates.csv)
    Note: as an initial step. For each sampled question injects the question into randomly chosen template to frame a final input RQ4 question.
    Step 3) saves output for every 50 rows to minimize data loss on failure. (temp output written to "/data/runtime_partitioned/rq4*.csv")
    Step 4) concatinates the partitioned files saved on step 3 to form a final RQ4 base data file (saved to /data/generated/RQ4_base.xlsx)
    
    Args:
        llm (str, optional): "gpt" uses 3.5 turbo or "PALM" (not maintained). Defaults to "gpt".

    Raises:
        Exception: raises any runtime exception.
    """
    
    try:
        logger.info("RQ4_NEW_START") 
        language_mapping = dict(pd.read_csv("./data/base/language.csv", header=None).values)
        languages = language_mapping.keys()
        writer = None
        record_count = 0
        max_records_per_file = 1
        
        data = pd.read_excel("./data/generated/RQ4_input.xlsx")
        data["RQ1_lang_code"] = data["RQ1_lang_code"].fillna("N_A").astype(str)
        tempaltes =  pd.read_csv("./data/processed/RQ4_template_input.csv")
        inputs = data.apply(lambda x : (x["Input"], x["Final Question"] , x["Language"], x["Language Code"], x["Source RQ"], x["RQ1_lang_code"]), axis = 1)
        for input in inputs[:3]:
            base_question = input[0]
            final_question = input[1]
            langauge = input[2]
            language_code = input[3]
            source_rq = input[4]
            rq1_code = input[5]
            # if not rq1_code:
            #     rq1_code
            random_template_row = tempaltes.sample()
            template_number = random_template_row.index[0]
            template_name = random_template_row["Template Name"][template_number]
            template_link = random_template_row["Link"][template_number]
            template_text = random_template_row["Prompt Template"][template_number]
            language_force_tag = ""
            if source_rq == "RQ1":
                language_force_tag = f". (Please answer my question in {langauge})"
            final_templated_prompt = template_text.replace("INSERT PROMPT HERE", final_question + language_force_tag)
            str_num = str(template_number)
            row = [source_rq, base_question, langauge, language_code, final_question, rq1_code, str_num, template_name, template_link, final_templated_prompt]
            if llm == "gpt":
                llm_response = chatgpt_response(final_templated_prompt)[:5000]
            if llm == "palm":
                llm_response = palm_response(final_templated_prompt)[:5000]
            row = row + [llm_response]
            gpt_eng_input = cloudTranslate("en", llm_response, language_codes)
            row = row + [gpt_eng_input]
            if record_count % max_records_per_file == 0:
                if writer:
                    f.close()
                file_num = record_count // max_records_per_file + 1
                file_name = f'./data/runtime_partitioned/rq45_{file_num}.csv'
                f = open(file_name, 'w')
                writer = csv.writer(f)
                writer.writerow(["Source RQ", "Base_Question", "Language", "Lang code", "RQ 123 Final Question", "Ori RQ1 lang", "Template Number","Template Number", "Template Link", "Final Prompt", "ChatGPT's Answer", "English Answer", "TimeStamp"])
            writer.writerow(row + [datetime.now().isoformat()])
            logger.info("|-|".join(row + [datetime.now().isoformat()])) 
            record_count += 1
        f.close()
        logger.info("aggregating partitioned files...") 
        files = glob.glob("./data/runtime_partitioned/rq45_*.csv")
        df_list = []
        for file in files:
            df = pd.read_csv(file)
            df_list.append(df)
        aggregated_df = pd.concat(df_list)
        aggregated_df.to_excel("./data/generated/RQ4_base.xlsx", index=False)
        logger.info("RQ4_END") 
    except:
        raise Exception("crashed while running")
    finally:
        f.close()
     

# main method
if __name__ == '__main__':
    languages = get_supported_languages("en")
    language_codes =  [x.language_code for x in languages]
    # rq1("gpt")
    # rq2("gpt")
    # rq3("gpt")
    # rq4InputGen()
    rq4("gpt")
