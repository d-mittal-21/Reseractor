from nltk import FreqDist
import nltk
# nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import pandas as pd
import numpy as np
from nltk import pos_tag
import re
from typing import List, Dict, Tuple
import sqlite3

class ExperimentalDataExtractor:
    def __init__(self):
        self.number_pattern = r'[-+]?\d*\.?\d+'
        self.measurement_pattern = None
        self.search_terms = []
        self.window_size = 5
        
    def set_parameters(self, search_terms: List[str], units: List[str]):
        self.search_terms = [term.strip().lower() for term in search_terms]
        # Create regex pattern for measurements with units
        units_pattern = '|'.join(map(re.escape, units))
        self.measurement_pattern = f"{self.number_pattern}\s*({units_pattern})"
        
    def extract_data_from_text(self, text: str, doc_id: int) -> List[Dict]:
        results = []
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # First check if sentence contains any search terms
            if not any(term in sentence_lower for term in self.search_terms):
                continue
            
            # Find all numbers with units
            matches = list(re.finditer(self.measurement_pattern, sentence))
            if not matches:
                continue
            
            # Process each measurement found
            for match in matches:
                full_match = match.group(0)
                value = float(re.search(self.number_pattern, full_match).group())
                unit = match.group(1)
                
                # Find which search term this measurement relates to
                for term in self.search_terms:
                    if term in sentence_lower:
                        results.append({
                            'doc_id': doc_id,
                            'parameter': term,
                            'value': value,
                            'unit': unit,
                            'sentence': sentence
                        })
        
        return results

def extract_experimental_data(search_terms: List[str], 
                            selected_topics: List[str],
                            units: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    try:
        # Initialize extractor
        extractor = ExperimentalDataExtractor()
        extractor.set_parameters(search_terms + selected_topics, units)
        
        # Get text from database
        conn = sqlite3.connect('database/articles.db')
        df = pd.read_sql_query("SELECT id, text FROM articles", conn)
        conn.close()
        
        all_results = []
        for _, row in df.iterrows():
            results = extractor.extract_data_from_text(row['text'], row['id'])
            all_results.extend(results)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(all_results)
        print("Found results:", len(all_results))  # Debug print
        
        if not results_df.empty:
            # Create summary view
            summary_df = results_df.groupby(['doc_id', 'parameter', 'unit'])['value'].agg(list).reset_index()
            
            # Create pivot table
            pivot_df = pd.pivot_table(
                summary_df,
                index='doc_id',
                columns=['parameter', 'unit'],
                values='value',
                aggfunc='first'  # Changed from lambda x: x to 'first'
            ).reset_index()
            
            # Flatten column names
            pivot_df.columns = [f"{col[0]}_{col[1]}_{col[2]}" if isinstance(col, tuple) and len(col) == 3 
                              else (f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col) 
                              for col in pivot_df.columns]
            
            return results_df, pivot_df
        
        return pd.DataFrame(), pd.DataFrame()
        
    except Exception as e:
        print(f"Error in data extraction: {e}")
        return pd.DataFrame(), pd.DataFrame()


def taging(lemm):
  tags = nltk.pos_tag(lemm)
  return tags

#creating sentence tokens
def sen_tok(sents):
  sentences = sent_tokenize(sents)
  r = 0
  final = []
  cd_sent = ""
  ref = ""
  s_tag=[]
  s_pos=[]
  for s in sentences:
    words = word_tokenize(s)
    s_tag = taging(words)
    s_pos = [pos for w, pos in s_tag]
    #separating sentences containing cardinal tags
    if 'CD' in s_pos and r!=1:
      cd_sent+= s
    #separating for references
    if 'References' in words or r==1:
      r=1
      ref+= s
    final+=words
  return ref, final, cd_sent

#lemmatization
def lemmat(filtered):
  lemma = WordNetLemmatizer()
  lemm = [lemma.lemmatize(word,pos="v") for word in filtered]
  return lemm

#removing stop words, lemmatizing filtered text
def preprocess(txt):
  stop_words = set(stopwords.words("english"))
  ref, sent_words, cd_sent = sen_tok(txt)
  # print(stop_words)
  filtered = [word for word in sent_words if word.casefold() not in stop_words]
  # print(filtered)
  lemm = lemmat(filtered)
  return lemm,ref,cd_sent

#filter lemmatized text from punctuations
def filter(txt):
  #punctuation = ['!','"','#','$','%','&','\'','(',')','*','+',',','-','.','/',':',';','<','=','>','?','@','[','\',']','^','_','`','{','|','}','~']
  import string
  spunct = string.punctuation
  lpunct = []
  lpunct[:0] = spunct
  lpunct+= '±'
  lpunct.remove('%')
  filtered = [tok for tok in txt if tok not in lpunct]
  return filtered

def topic_extract(ids):
  success = True
  try:
    conn = sqlite3.connect('database/articles.db')
    c = conn.cursor()

    # Prepare the query with placeholders for the ids
    placeholders = ', '.join('?' for id in ids)
    query = f"SELECT text FROM articles WHERE id IN ({placeholders})"
    c.execute(query, ids)
    texts = [row[0] for row in c.fetchall()]
    top5_input = ""
    for text in texts:
      top5_input += str(text)
    text= []
    t_card = ""
    references = ""
    pgtxt,ref,cd_sent = preprocess(top5_input)
    t_card+=cd_sent
    references+=ref
    text+= pgtxt
    f_text = filter(text)
    c.execute('''
        CREATE TABLE IF NOT EXISTS f_text_table (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
    ''')
    c.executemany('INSERT INTO f_text_table (value) VALUES (?)', [(value,) for value in f_text])

    # Commit the changes and close the connection
    conn.commit()
    frequency_distribution = FreqDist(f_text)
    mc = frequency_distribution.most_common(30)
    mc_n = [row[0] for row in mc]
    tags = taging(mc_n)
    f_mc = [word for word,pos in tags if not ( (len(word)<3) or (pos == 'CD'))]
    freq = []
    for row in mc:
      if row[0] in f_mc:
        freq.append(row[1])
    conn.close()
    units_sear = ['kg','g','kgf','gf','N','kN','mg','°C','μL','ns','g/cm3','kg/m3','K','%','nm','cm','°','h','M','ml','rpm','°/min','mg/ml']
    return f_mc, units_sear, success
  except Exception as e:
    print(e)
    success = False
    return None, None, success
  
def condition_extraction(search):
  success = True
  try:
    conn = sqlite3.connect('database/articles.db')
    c = conn.cursor()

    # Execute a query to select all the values from the f_text_table table
    c.execute('SELECT value FROM f_text_table')

    # Fetch all the rows and extract the value column from each row
    f_text = [row[0] for row in c.fetchall()]
    count = 0
    w = -50
    l = len(f_text)
    conditions = []
    units_sear = ['kg','g','kgf','gf','N','kN','mg','°C','μL','ns','g/cm3','kg/m3','K','%','nm','cm','°','h','M','ml','rpm','°/min','mg/ml']
    for tok in f_text:
      count+=1
      minimum = max(0,count-50)
      maximum = min(count+50,l)
      if tok in search:
        if count-w<49:
          minimum = w+49
        w=count
        for j in range(minimum,maximum):
          tag = taging([f_text[j]])
          pos = tag[0][1]
          #print(pos)
          if pos == 'CD' and (f_text[j+1]) in units_sear:
            if j>=2 and j<l-2:
              conditions.append(tok + " : " + f_text[j-2] + " " + f_text[j-1] + " " + f_text[j] + " " + f_text[j+1] + " " + f_text[j+2])
            elif j<2:
              conditions.append(tok + " : " + f_text[j] + " " + f_text[j+1] + " " + f_text[j+2])  
              # print(tok, ":", f_text[j], f_text[j+1], f_text[j+2])
            elif j==l-2:
              conditions.append(tok + " : " + f_text[j] + " " + f_text[j+1])
              # print(tok, ":", f_text[j], f_text[j+1])
    conn.close()
    return conditions, success
  except Exception as e:
    print(e)
    success = False
    return None, success
