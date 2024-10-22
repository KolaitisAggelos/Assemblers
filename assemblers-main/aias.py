import cohere
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from api import API_KEY
from db import conn
import json, wikipedia
from get_articles import get_links, get_text, save_file


# flask = Flask(__name__)

model="embed-english-v3.0"

co = cohere.Client(API_KEY)

cursor = conn.cursor()

def embed_text(text):
    # Create basic configurations to chunk the text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )

    # Split the text into chunks with some overlap
    chunks_ = text_splitter.create_documents([text])
    chunks = [c.page_content for c in chunks_]
    print(f"The text has been broken down in {len(chunks)} chunks.")

    response = co.embed(
        texts= chunks,
        model=model,
        input_type="search_document",
        embedding_types=['float']
    )
    embeddings = response.embeddings.float
    print(f"We just computed {len(embeddings)} embeddings.")

    

    in_vectors = [[embeddings[i][j] for j in range(len((embeddings[i])))] for i in range(len(embeddings))]

    # print(in_vectors)
    for i in range(len(chunks)):
        cursor.execute(f"INSERT INTO vectors (original, vector) VALUES (%s, %s)", (chunks[i], json.dumps(in_vectors[i])))

def run_query(query):
    response = co.embed(
        texts=[query],
        model=model,
        input_type="search_query",
        embedding_types=['float']
    )
    query_embedding = response.embeddings.float[0]

    cursor.execute("SELECT vector FROM vectors")
    res = cursor.fetchall()
    embeddings = [json.loads(x[0]) for x in res]

    cursor.execute("SELECT original FROM vectors")

    chunks = cursor.fetchall()

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Calculate similarity between the user question & each chunk
    similarities = [cosine_similarity(query_embedding, chunk) for chunk in embeddings]

    # Get indices of the top 10 most similar chunks
    sorted_indices = np.argsort(similarities)[::-1]

    # Keep only the top 10 indices
    top_indices = sorted_indices[:10]
    # print(chunks)
    # print("Here are the indices of the top 10 chunks after retrieval: ", top_indices)

    # Retrieve the top 10 most similar chunks
    top_chunks_after_retrieval = [chunks[i][0] for i in top_indices]
    # print("Here are the top 10 chunks after retrieval: ")
    # for t in top_chunks_after_retrieval:
    #     print("== " + t)

    response = co.rerank(
        query=query,
        documents=top_chunks_after_retrieval,
        top_n=3,
        model="rerank-english-v2.0",
    )

    top_chunks_after_rerank = [result.document['text'] for result in response]
    # print("Here are the top 3 chunks after rerank: ")
    # for t in top_chunks_after_rerank:
    #     print("== " + t)

    preamble = """
    ## Task & Context
    You help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of news articles or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging.You should choose the most important information out of the given request's keywords.

    ## Style Guide
    Unless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling.
    """

    # retrieved documents
    documents = [
        {"title": "chunk" + str(i), "snippet": top_chunks_after_rerank[i]} for i in range(len(top_chunks_after_rerank))
      ]

    # get model response
    response = co.chat(
      message=query,
      documents=documents,
      preamble=preamble,
      model="command-r",
      temperature=0.3
    )

    print("Final answer:")
    print(response.text)

    save = input("Save answer? (y/n): ")
    if save.lower() in ["y", "yes"]:
        tp = int(input("\n1. PDF\n2. JSON\n3. TXT\n"))
        if tp == 1:
            save_file(input('Filename (.pdf will be added): '), response.text, 'pdf')
        elif tp == 2:
            save_file(input('Filename (.json will be added): '), response.text, 'json', query)
        elif tp == 3:
            save_file(input('Filename (.txt will be added): '), response.text, 'txt')
        

if __name__ == "__main__":
    cursor.execute("CREATE TABLE IF NOT EXISTS vectors (\
                   id INT PRIMARY KEY NOT NULL,\
                   original TEXT,\
                   vector TEXT\
                   )")
    while True:
        try:
            option = int(input("\n1. Feed data\n2. Run query\n3. Clear database\n4. Exit\n"))
        except ValueError:
            continue

        if option == 1:
            ans = int(input("\n1. Wikipedia\n2. Articles\n3. Text input\n"))
            if ans == 1:
                while True:
                    try:
                        page_content = wikipedia.page(input("Wiki: ")).content
                    except wikipedia.exceptions.PageError:
                        print("Please enter a valid text to embed.")
                    else:
                        embed_text(page_content)
                        break
            elif ans == 2:

                category = str(input("Give me a category (technology / finance / politics etc.): "))   #ΚΑΤΗΓΟΡΙΑ ΘΕΜΑΤΟΣ

                stop = int(input("Stop at page: "))

                for page_var in range(stop + 1):
                    current_page = "https://www.skai.gr/news/{}?page={}".format(category, page_var)

                    current_source = "https://www.skai.gr/"
                    links = [current_source + l for l in get_links(current_page)]

                    text = get_text(links, input("Wanted year: "))
                    print(text)
                    embed_text(text)

            elif ans == 3:
                text = input("Text to embed: \n")
                embed_text(text)
            else:
                print("Invalid option")
        elif option == 2:
            query = input("Enter query: ")
            run_query(query)
        elif option == 3:
            if input("Are you sure? (y/n) ").lower() in ['y', 'yes']:
                cursor.execute("DELETE FROM vectors")
        elif option == 4:
            break
        else:
            print("Invalid option")
        conn.commit()
    conn.close()