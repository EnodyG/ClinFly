import json
import streamlit as st
from .web_utilities import st_cache_data_if, supported_cache
from pdf2image import convert_from_bytes, convert_from_path
import pytesseract

@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def convert_df(df):
    return df.dropna(how="all").to_csv(sep="\t", index=False).encode("utf-8")


@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def convert_df_no_header(df):
    return (
        df.dropna(how="all").to_csv(sep="\t", index=False, header=None).encode("utf-8")
    )


@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def convert_json(df,omop_value):
    dict_return = {"features": []}
    df_check = df.dropna(subset=["HPO ID", "Phenotype name"])
    if len(df_check) > 0:
        if omop_value == True:
            df_dict_list = df[["HPO ID", "Phenotype name","Omop Concept Id","Omop Concept Name","Omop Concept Code","Omop Concept Vocab"]].to_dict(orient="index")
            for key, value in df_dict_list.items():
                dict_return["features"].append(
                    {
                        "id": value["HPO ID"],
                        "observed": "yes",
                        "label": value["Phenotype name"],
                        "type": "phenotype",
                        "omop concept id" : value["Omop Concept Id"],
                        "omop concept name" : value["Omop Concept Name"],
                        "omop concept code" : value["Omop Concept Code"],
                        "omop concept vocab" : value["Omop Concept Vocab"]
                    }
            )
        else:
            df_dict_list = df[["HPO ID", "Phenotype name"]].to_dict(orient="index")
            for key, value in df_dict_list.items():
                dict_return["features"].append(
                    {
                        "id": value["HPO ID"],
                        "observed": "yes",
                        "label": value["Phenotype name"],
                        "type": "phenotype",
                    }
                )
        return json.dumps(dict_return)
    else:
        return json.dumps(dict_return)

@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def convert_list_phenogenius(df,omop_value):
    df_check = df.dropna(subset=["HPO ID", "Phenotype name"])
    if len(df_check) > 0:
        if omop_value == True:
            list = []
            for _, row in df_check.iterrows():
                if row['Omop Concept Id'] == 'None':
                    list.append(f"{row['HPO ID']}/OMOP:{row['Omop Concept Name']}")
                else:
                    list.append(f"{row['HPO ID']}/OMOP:{row['Omop Concept Id']}")
            return "\n".join(list)
        else:
            return ",".join(df_check["HPO ID"].to_list())
    else:
        return "No HPO in letters."

@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def convert_pdf_to_text(file):
    if isinstance(file, bytes):
        images = convert_from_bytes(file)
    else:
        images = convert_from_path(file)
    extraction = []
    for img in images:
        text = pytesseract.image_to_string(img)
        extraction.append(text)
    
    return " ".join(extraction)