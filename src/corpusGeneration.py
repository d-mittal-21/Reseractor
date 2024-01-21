def correct_text(input_text):
    words = nltk.word_tokenize(input_text.lower())
    corrected_words = []

    for word in words:
        if word not in brown.words():
            corrected_words.append("[ERR]")
        else:
            corrected_words.append(word)

    corrected_text = " ".join(corrected_words)
    return corrected_text

def is_number_token(token):
    try:
        float(token)
        return True
    except ValueError:
        return False
    
    
def preprocess(text):
  text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")

  # Remove string expressions like [1], [1,2,3,4], etc.
  cleaned_text = re.sub(r'\[\d+(,\s*\d+)*\]', '', text)
  #print(cleaned_text)

  # Tokenize the cleaned text into words
  tokens = word_tokenize(cleaned_text)

  # Convert words to lowercase
  lowercase_tokens = [token.lower() for token in tokens]

  # Remove stopwords and punctuation only tokens
  stop_words = set(stopwords.words('english'))
  punctuations = set(string.punctuation)

  filtered_tokens = [token for token in tokens if token.lower() not in stop_words and token.lower() not in punctuations and not is_number_token(token) and len(token) > 1]

  # Lemmatize the tokens
  lemmatizer = WordNetLemmatizer()
  lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]

  return lemmatized_tokens


