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

