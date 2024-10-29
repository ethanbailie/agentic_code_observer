from embed_pr import embedder
from dotenv import load_dotenv

load_dotenv()

## github params
owner = 'ethanbailie'
repo = 'agentic_code_observer'

## add embeddings to pinecone
embedder = embedder()
recent_pull_requests = embedder.fetch_recent_prs(owner=owner, repo=repo, hours_ago=36)
embed_vectors = embedder.embed_pr_data(recent_pull_requests)
embedder.upsert_to_pinecone(embed_vectors, index_name='rootly')


