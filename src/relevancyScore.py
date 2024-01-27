import sqlite3
import numpy as np
import cv2
import os
import pytesseract
from PIL import Image as Img
from pdf2image import convert_from_path
import time
from sent2vec.vectorizer import Vectorizer
import pandas as pd
import torch
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
from transformers import BertTokenizer
import json

def test_function():
  # Set the folder path containing the PDFs
  folder_path = '/content/drive/MyDrive/UG_ML/Testing'

  # Initialize an empty dataframe
  df = pd.DataFrame(columns=['PDF', 'Abstract'])

  # Loop through each PDF in the folder
  for filename in os.listdir(folder_path):
      if filename.endswith('.pdf'):
          pdf_path = os.path.join(folder_path, filename)

          # Convert the first page of the PDF to an image
          images = convert_from_path(pdf_path, first_page=1, last_page=2)
          image_path = '/content/first_page.jpg'
          images[0].save(image_path, 'JPEG')
          time.sleep(1)

          # Perform OCR on the image
          extracted_text = pytesseract.image_to_string(Img.open(image_path))

          # Find the abstract section on the first page
          start_index = extracted_text.find('Abstract') + len('Abstract')
          end_index = extracted_text.find('Introduction')

          if start_index == -1 or end_index == -1:
              # Abstract and/or Introduction not found on first page
              # Find the abstract section on the second page
              extracted_text = pytesseract.image_to_string(images[1])

              start_index = extracted_text.find('Abstract') + len('Abstract')
              end_index = extracted_text.find('Introduction')

              if start_index == -1 or end_index == -1:
                  # Abstract and/or Introduction not found on second page
                  abstract = 'NaN'
              else:
                  # Extract abstract from the second page
                  abstract = extracted_text[start_index:end_index].strip()
          else:
              # Extract abstract from the first page
              abstract = extracted_text[start_index:end_index].strip()

          # Add the abstract and PDF name to the dataframe
          df = df.append({'PDF': filename, 'Abstract': abstract}, ignore_index=True)
  return df

def generate_embeddings(text, vectorizer):
    list = []
    list.append(text)
    vectorizer.run(list)
    vectors = vectorizer.vectors
    return vectors[-1]

def check_relevancy(df, relevancy_params, search_term):
    # Compute the cosine similarity between the search term and the title and abstract embeddings
    df['title_similarity'] = df['title_embedding'].apply(lambda x: np.dot(x, search_term) / (np.linalg.norm(x) * np.linalg.norm(search_term)))
    df['abstract_similarity'] = df['abstract_embedding'].apply(lambda x: np.dot(x, search_term) / (np.linalg.norm(x) * np.linalg.norm(search_term)))
    
    # loading model
    model = torch.load('models/reseractor_model.pth')
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    prediction_list = []
    prediction_score = []
    for abstract in df['abstract']:
        predicted_labels = []

        all_inputs=[]
        t_sum = 0
        f_sum = 0
        sentences = sent_tokenize(abstract)
        for sentence in sentences:

            input_ids = tokenizer.encode(sentence, add_special_tokens=True)


            inputs = torch.tensor(input_ids).unsqueeze(0)


            with torch.no_grad():
                outputs = model(inputs)
                _, predicted_label = torch.max(outputs[0], 1)

            all_inputs.append(inputs)
            predicted_labels.append(predicted_label.item())
            if(predicted_label.item() == 1):
                t_sum += 1
            else:
                f_sum += 1
        score = t_sum/(t_sum + f_sum)
        prediction_score.append(score)
        prediction_list.append(predicted_labels)
    df['p_score'] = prediction_score
    print(df['p_score'])
    # Compute the relevancy score
    df['relevancy_score'] = 4.5*df['title_similarity'] + 4.5*df['abstract_similarity'] + 1*df['p_score']
    print(df['relevancy_score'])
    # Sort the dataframe by the relevancy score
    df_sorted = df.sort_values(by='relevancy_score', ascending=False)
    return df_sorted

def relevancy_table(relevancy_params, search_term):
    success = True
    try:
        conn = sqlite3.connect('database/articles.db')
        c = conn.cursor()
        vectorizer = Vectorizer()
        
        c.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in c.fetchall()]
        if 'title_embedding' not in columns:
            c.execute("ALTER TABLE articles ADD COLUMN title_embedding TEXT")
        if 'abstract_embedding' not in columns:
            c.execute("ALTER TABLE articles ADD COLUMN abstract_embedding TEXT")

        # Select all rows from the articles table
        c.execute("SELECT * FROM articles")
        rows = c.fetchall()

        for row in rows:
            id, text, title, abstract, text_corpora, title_embedding, abstract_embedding = row

            # Compute the vector embeddings for the title and abstract
            title_embedding = generate_embeddings(title, vectorizer)
            abstract_embedding = generate_embeddings(abstract, vectorizer)
            print(1)
            title_embedding_json = json.dumps(title_embedding.tolist())
            abstract_embedding_json = json.dumps(abstract_embedding.tolist())
            # Update the articles table with the embeddings
            c.execute("""
                UPDATE articles
                SET title_embedding = ?, abstract_embedding = ?
                WHERE id = ?
            """, (title_embedding_json, abstract_embedding_json, id))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        # Get an instance of the table in a dataframe
        conn = sqlite3.connect('database/articles.db')
        df = pd.read_sql_query("SELECT * FROM articles", conn)
        df['title_embedding'] = df['title_embedding'].apply(json.loads)
        df['abstract_embedding'] = df['abstract_embedding'].apply(json.loads)

        # Convert the lists to numpy arrays
        df['title_embedding'] = df['title_embedding'].apply(np.array)
        df['abstract_embedding'] = df['abstract_embedding'].apply(np.array)
        conn.close()
        search_term_embedding = generate_embeddings(search_term, vectorizer)
        df_sorted = check_relevancy(df, relevancy_params, search_term_embedding)
        ids = df_sorted['id'].tolist()
        return ids, success
    except Exception as e:
        print(e)
        success = False
        return None, success


