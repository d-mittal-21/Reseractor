from nltk import FreqDist

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
  print(stop_words)
  filtered = [word for word in sent_words if word.casefold() not in stop_words]
  print(filtered)
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
    return f_mc, success
  except Exception as e:
    print(e)
    success = False
    return None, success
  
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
