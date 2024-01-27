from sent2vec.vectorizer import Vectorizer
import numpy as np
text = "hello me"
text_list = []
text_list.append(text)
vectorizer = Vectorizer()
vectorizer.run(text_list)
vectors = vectorizer.vectors
print(len(vectors))