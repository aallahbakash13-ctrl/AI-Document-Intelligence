from fastembed import TextEmbedding

model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

texts = [
    "Artificial Intelligence is transforming technology.",
    "Machine Learning is a part of Artificial Intelligence."
]

embeddings = list(model.embed(texts))

print("Total embeddings:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))
print("First embedding:", embeddings[0][:5])