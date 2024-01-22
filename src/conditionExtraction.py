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
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()

    # Prepare the query with placeholders for the ids
    placeholders = ', '.join('?' for id in ids)
    query = f"SELECT text FROM articles WHERE id IN ({placeholders})"
    c.execute(query, ids)
    texts = [row[0] for row in c.fetchall()]
    conn.close()
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
    frequency_distribution = FreqDist(f_text)
    mc = frequency_distribution.most_common(30)
    mc_n = [row[0] for row in mc]
    tags = taging(mc_n)
    f_mc = [word for word,pos in tags if not ( (len(word)<3) or (pos == 'CD'))]
    freq = []
    for row in mc:
      if row[0] in f_mc:
        freq.append(row[1])
    
    return f_mc, success
  except Exception as e:
    print(e)
    success = False
    return None, success
