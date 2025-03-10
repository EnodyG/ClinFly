import pandas as pd
from .web_utilities import st_cache_data_if, supported_cache

@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def from_omop_to_hpo(omop_code, omop_file='OMOP2OBO_V1.5_Condition_Occurrence_Mapping_Oct2020.xlsx'):
    # Lire la feuille spécifique du fichier Excel
    df_omop = pd.read_excel(omop_file, sheet_name='OMOP2OBO_HPO_Mapping_Results')
    
    # Trouver la ligne correspondant au code OMOP
    row = df_omop[df_omop['CONCEPT_ID'] == omop_code]
    
    if not row.empty:
        # Extraire les colonnes ONTOLOGY_LOGIC, ONTOLOGY_URI, ONTOLOGY_LABEL, MAPPING_CATEGORY
        result = row[['ONTOLOGY_LOGIC', 'ONTOLOGY_URI', 'ONTOLOGY_LABEL', 'MAPPING_CATEGORY']].iloc[0]
        return result.to_dict()
    else:
        return "No match between the omop concept id " + omop_code + " and HPO"

@st_cache_data_if(supported_cache, max_entries=10, ttl=3600)
def from_hpo_to_omop(hpo_code, hpo_file='hp.ols.sssom.tsv', omop_file='OMOP2OBO_V1.5_Condition_Occurrence_Mapping_Oct2020.xlsx'):
    # Lire le fichier TSV en ignorant les lignes de commentaire
    df_hpo = pd.read_csv(hpo_file, sep='\t', comment='#')
    
    # Trouver les lignes correspondant au code HPO
    rows_hpo = df_hpo[df_hpo.iloc[:, 0] == hpo_code]

    if rows_hpo.empty:
        return "No match for HPO code : " + hpo_code 
    
    # Extraire les object_id correspondants qui commencent par SNOMEDCT_US
    snomed_codes = [object_id.split(':')[1] for object_id in rows_hpo.iloc[:, 2] if object_id.startswith('SNOMEDCT_US:')]

    if not snomed_codes:
        return "No link between HPO and Snomed code for HPO code : " + hpo_code

    # Lire la feuille spécifique du fichier Excel OMOP
    df_omop = pd.read_excel(omop_file, sheet_name='OMOP2OBO_HPO_Mapping_Results')

    results = []
    for snomed_code in snomed_codes:
        # Trouver les lignes correspondant au code SNOMED dans OMOP
        row_omop = df_omop[df_omop['CONCEPT_CODE'] == int(snomed_code)]
        
        if not row_omop.empty:
            # Extraire les colonnes CONCEPT_ID, CONCEPT_NAME, et ANCESTOR_CONCEPT_ID
            result = row_omop[['CONCEPT_ID', 'CONCEPT_NAME','CONCEPT_CODE','CONCEPT_VOCAB', 'ANCESTOR_CONCEPT_ID']].iloc[0]
            result['ANCESTOR_CONCEPT_ID'] = [int(x) for x in result['ANCESTOR_CONCEPT_ID'].split('|')]  # Conversion en liste d'entiers
            results.append(result.to_dict())
        else:
            return "No link between the Snomed code " + snomed_code + " and the OMOP database"

    #On retire les redondances dans les ancestors id
    for result in results:
        ancestor_ids = result['ANCESTOR_CONCEPT_ID']
        concept_id = result['CONCEPT_ID']
        if concept_id in ancestor_ids:
            ancestor_ids.remove(concept_id) 
    
    final_results = []

    #On ajoute une clé qui indique si l'élément analysé se trouve dans les ancêtres des autres éléments du dictionnaire
    for result in results:
        for other_result in results:
            if result['CONCEPT_ID'] in other_result['ANCESTOR_CONCEPT_ID']:
                result['LOWER'] = False
                break

    #On récupère uniquement les éléments les plus profonds et donc les termes les plus précis
    for result in results:
        if len(result) == 5:
            del result['ANCESTOR_CONCEPT_ID']
            final_results.append(result)          
    
    final_results = {key: [d[key] for d in final_results] for key in final_results[0]}
    return final_results