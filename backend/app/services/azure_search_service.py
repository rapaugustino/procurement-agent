"""
Azure Search Service for document retrieval.
Migrated from notebook code with improved modularity.
"""

import requests
from typing import List
from langchain_core.documents import Document


class AdaptiveHybridAzureSearchRetriever:
    """
    Adaptive hybrid search retriever that combines vector and keyword search
    with automatic semantic search detection.
    """
    
    def __init__(self, search_service: str, search_key: str, index_name: str, embeddings):
        self.search_service = search_service
        self.search_key = search_key
        self.index_name = index_name
        self.embeddings = embeddings
        self.search_url = f"https://{search_service}.search.windows.net/indexes/{index_name}/docs/search"
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': search_key
        }
        self.semantic_available = None  # Will be detected on first use
    
    def _check_semantic_availability(self) -> bool:
        """Check if semantic search is configured for this index"""
        if self.semantic_available is not None:
            return self.semantic_available
            
        # Get index configuration to check for semantic search
        index_url = f"https://{self.search_service}.search.windows.net/indexes/{self.index_name}?api-version=2023-11-01"
        response = requests.get(index_url, headers=self.headers)
        
        if response.status_code == 200:
            index_config = response.json()
            semantic_config = index_config.get('semantic', {})
            configurations = semantic_config.get('configurations', [])
            
            if configurations:
                self.semantic_available = True
                self.semantic_config_name = configurations[0].get('name', 'default')
                print(f"✅ Semantic search detected - using config: {self.semantic_config_name}")
            else:
                self.semantic_available = False
                print("ℹ️  No semantic search configured - using standard hybrid search")
        else:
            self.semantic_available = False
            print("⚠️  Could not check semantic config - using standard hybrid search")
            
        return self.semantic_available
    
    def invoke(self, query: str) -> List[Document]:
        """Perform ADAPTIVE HYBRID search with semantic support when available"""
        
        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Check semantic availability
        has_semantic = self._check_semantic_availability()
        
        # Build search body - start with hybrid (vector + keyword)
        search_body = {
            "search": query,  # Keyword/BM25 search component
            "vectorQueries": [{
                "kind": "vector",
                "vector": query_embedding,
                "fields": "text_vector",
                "k": 10  # Get more candidates for reranking
            }],
            "select": "chunk_id,chunk,title,parent_id",
            "top": 5,  # Final number of results
        }
        
        # Add semantic search if available
        if has_semantic:
            search_body.update({
                "queryType": "semantic",
                "semanticConfiguration": self.semantic_config_name,
                "captions": "extractive",  # Get highlighted captions
                "answers": "extractive"   # Get direct answers when possible
            })
        
        response = requests.post(f"{self.search_url}?api-version=2023-11-01", 
                               headers=self.headers, 
                               json=search_body)
        
        if response.status_code == 200:
            results = response.json()
            documents = []
            
            search_type = "SEMANTIC HYBRID" if has_semantic else "STANDARD HYBRID"
            print(f"✅ {search_type} SEARCH SUCCESS - Combined vector + keyword search")
            
            for doc in results.get('value', []):
                # Extract captions if available (semantic search feature)
                captions = doc.get('@search.captions', [])
                caption_text = captions[0].get('text', '') if captions else ''
                
                document = Document(
                    page_content=doc.get('chunk', ''),
                    metadata={
                        'chunk_id': doc.get('chunk_id', ''),
                        'title': doc.get('title', ''),
                        'parent_id': doc.get('parent_id', ''),
                        'source': doc.get('title', 'Azure Search'),
                        'search_score': doc.get('@search.score', 0),
                        'reranker_score': doc.get('@search.rerankerScore', 0) if has_semantic else 0,
                        'caption': caption_text
                    }
                )
                documents.append(document)
            
            return documents
        else:
            # Fallback to vector-only search if hybrid fails
            print(f"Hybrid search failed ({response.status_code}), falling back to vector-only")
            return self._vector_only_search(query)
    
    def _vector_only_search(self, query: str) -> List[Document]:
        """Fallback vector-only search"""
        query_embedding = self.embeddings.embed_query(query)
        
        search_body = {
            "vectorQueries": [{
                "kind": "vector",
                "vector": query_embedding,
                "fields": "text_vector",
                "k": 5
            }],
            "select": "chunk_id,chunk,title,parent_id"
        }
        
        response = requests.post(f"{self.search_url}?api-version=2023-11-01", 
                               headers=self.headers, 
                               json=search_body)
        
        if response.status_code == 200:
            results = response.json()
            documents = []
            
            print("⚠️  Using vector-only search (still very good results)")
            
            for doc in results.get('value', []):
                document = Document(
                    page_content=doc.get('chunk', ''),
                    metadata={
                        'chunk_id': doc.get('chunk_id', ''),
                        'title': doc.get('title', ''),
                        'parent_id': doc.get('parent_id', ''),
                        'source': doc.get('title', 'Azure Search')
                    }
                )
                documents.append(document)
            
            return documents
        else:
            print(f"Vector search also failed: {response.status_code}")
            return []
