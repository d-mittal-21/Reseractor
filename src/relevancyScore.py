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

def generate_embeddings(text):
    return 0

def relevancy_table(relevancy_params):
    success = True
    try:
        conn = sqlite3.connect('database/articles.db')
        c = conn.cursor()

        # Select all rows from the articles table
        c.execute("SELECT * FROM articles")
        rows = c.fetchall()

        for row in rows:
            id, text, title, abstract, text_corpora = row

            # Compute the vector embeddings for the title and abstract
            title_embedding = generate_embeddings(title)
            abstract_embedding = generate_embeddings(abstract)

            # Update the articles table with the embeddings
            c.execute("""
                UPDATE articles
                SET title_embedding = ?, abstract_embedding = ?
                WHERE id = ?
            """, (title_embedding, abstract_embedding, id))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        # Get an instance of the table in a dataframe
        conn = sqlite3.connect('database/articles.db')
        df = pd.read_sql_query("SELECT * FROM articles", conn)
        conn.close()
        ids = df['id'].tolist()
        return ids, success
    except Exception as e:
        print(e)
        success = False
        return None, success


