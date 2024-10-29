import requests
from datetime import datetime, timedelta, timezone
from langchain_cohere import CohereEmbeddings
from pinecone import Pinecone, ServerlessSpec
import os

class Embedder():
    '''
    embeds pr data from github and upserts to pinecone
    '''
    def __init__(self, model='embed-english-v3.0'):
        self.embeddings = CohereEmbeddings(model=model)
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.github_token = os.getenv('GITHUB_TOKEN')

    ## function to fetch all PRs
    def fetch_recent_prs(self, owner: str, repo: str, hours_ago: int) -> list:
        '''
        fetches all PRs from github and returns a list of dicts containing the retrieved PRs
        owner: str - the owner of the repo
        repo: str - the repo name
        hours_ago: int - the number of hours to go back to fetch PRs
        '''
        all_recent_prs = []

        ## pagination params
        params = {
            'state': 'all',
            'per_page': 100
        }
        page = 1

        ## build the pr url
        pr_url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
        headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        ## calculate the timestamp for 24 hours ago
        recency = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        recency_str = recency.isoformat() + 'Z'

        while True:
            params['page'] = page
            response = requests.get(pr_url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"Error: {response.status_code}. Ensure you have access to the repo with the provided credentials.")
                return []

            prs = response.json()

            ## filter on the recency param
            recent_prs = [pr for pr in prs if pr['updated_at'] >= recency_str]

            ## break if no more recent PRs are found
            if not recent_prs:
                break

            all_recent_prs.extend(recent_prs)
            page += 1

        ## put all details into a list of dicts
        all_prs = []

        for pr in all_recent_prs:
            if pr.get('merged_at'):
                pr_details = {
                    'id': pr['id'],
                    'title': pr['title'],
                    'state': pr['state'],
                    'description': pr['body'],
                    'updated_at': pr['updated_at'],
                    'url': pr['html_url']
                }

                ## fetch and display merge description if the PR was merged
                merge_commit_sha = pr['merge_commit_sha']
                commit_url = f'https://api.github.com/repos/{owner}/{repo}/commits/{merge_commit_sha}'
                commit_response = requests.get(commit_url, headers=headers).json()
                merge_description = commit_response.get('commit', {}).get('message', '')
                pr_details['merge_description'] = merge_description

                all_prs.append(pr_details)
        return all_prs

    def embed_pr_data(self, pr_data_list: list) -> list:
        '''
        embeds the pr data and returns a list of tuples containing the pr id, vector, and metadata
        pr_data_list: list - a list of dicts containing pr data
        '''
        ids = []
        texts = []
        metadatas = []
        if not pr_data_list:
            return []

        for pr in pr_data_list:
            pr_id = str(pr['id'])
            text_to_embed = f"Title: {pr['title']}. Description: {pr['description']}. Merge Description: {pr['merge_description']}."
            metadata = {
                'title': pr['title'],
                'state': pr['state'],
                'updated_at': pr['updated_at'],
                'url': pr['url']
            }
            ids.append(pr_id)
            texts.append(text_to_embed)
            metadatas.append(metadata)

        embeddings_list = self.embeddings.embed_documents(texts)

        vectors = []
        for pr_id, vector, metadata in zip(ids, embeddings_list, metadatas):
            vectors.append((pr_id, vector, metadata))

        return vectors

    def upsert_to_pinecone(self, vectors: list, index_name: str):
        '''
        upserts the vectors to pinecone
        vectors: list - a list of tuples containing the pr id, vector, and metadata
        index_name: str - the name of the index to upsert to
        '''
        if not vectors:
            return

        existing_index = [index['name'] for index in self.pc.list_indexes()]
        if index_name not in existing_index:
            self.pc.create_index(
                name=index_name,
                dimension=1024,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1',
                )
            )

        index = self.pc.Index(index_name)
        index.upsert(vectors)