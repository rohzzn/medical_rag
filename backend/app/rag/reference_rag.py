"""
Reference RAG Implementation - Exact replica of the Streamlit app logic
"""
import os
import re
import json
from openai import OpenAI
from typing import Dict, List, Any, Union

from app.rag.neo4j import Neo4jManager
from app.rag.embeddings import get_embedder
from app.core.config import settings

# Exact replica of the reference app's LLMHandler
class ReferenceLLMHandler:
    def __init__(self, retriever, api_key=None, model=None, temperature=None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature or 0.0
        self.retriever = retriever
        self.client = OpenAI(api_key=self.api_key)
        
    def _generate_completion(self, prompt, use_history=False):
        """Generate a completion using OpenAI API - updated for v1.0+"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating completion: {e}")
            return f"Error: {str(e)}"
    
    def _extract_sources(self, results):
        """Extract sources and their content from retriever results - exact replica"""
        sources = []
        source_contents = {}
        retriever_type = getattr(self.retriever, "__class__").__name__
        
        # Handle different types of retrievers - EXACT logic from reference app
        print(f"🔍 Extracting sources from {retriever_type} with {len(results.items)} items")
        
        if retriever_type == "VectorRetriever":
            for item in results.items:
                try:
                    content = item.content
                    print(f"📄 Vector item content: {str(content)[:200]}...")
                    data_dict = json.loads(content.replace("'", '"'))
                    source = data_dict.get("source2", "")
                    text = data_dict.get("text", "")
                    if source and source not in sources:
                        sources.append(source)
                        if text:
                            # Store or append the content for this source
                            if source in source_contents:
                                source_contents[source] += f"\n\n{text}"
                            else:
                                source_contents[source] = text
                        print(f"✅ Added vector source: {source}")
                except Exception as e:
                    print(f"❌ Error parsing vector item: {e}")
                    continue
        else:  # VectorCypherRetriever or HybridCypherRetriever
            for item in results.items:
                try:
                    content = str(item.content)
                    print(f"📄 Cypher item content: {content[:200]}...")
                    
                    # Extract sources - EXACT regex from reference
                    source_pattern = r"chunk_sources='(.*?)'(?=\s*truncated_relationship_texts=)"
                    source_match = re.search(source_pattern, content, re.DOTALL)
                    
                    # Extract text chunks - EXACT regex from reference  
                    text_pattern = r"truncated_chunk_texts='(.*?)'(?=\s*chunk_sources=)"
                    text_match = re.search(text_pattern, content, re.DOTALL)
                    
                    if source_match and text_match:
                        chunk_sources_text = source_match.group(1)
                        chunk_texts = text_match.group(1)
                        
                        print(f"📚 Found sources text: {chunk_sources_text[:100]}...")
                        print(f"📝 Found chunks text: {chunk_texts[:100]}...")
                        
                        # Split sources and texts - EXACT logic
                        chunk_sources = re.split(r'\\n---\\n', chunk_sources_text)
                        chunk_texts_list = re.split(r'\\n---\\n', chunk_texts)
                        
                        # Match sources with their content where possible - EXACT logic
                        for idx, source in enumerate(chunk_sources):
                            source = source.strip()
                            if source and source not in sources:
                                sources.append(source)
                                
                                # Try to get corresponding text if available
                                if idx < len(chunk_texts_list):
                                    text = chunk_texts_list[idx].strip()
                                    if text:
                                        source_contents[source] = text
                                print(f"✅ Added cypher source: {source}")
                    else:
                        print(f"❌ No source/text match found in: {content[:100]}...")
                except Exception as e:
                    print(f"❌ Error parsing cypher item: {e}")
                    continue
        
        print(f"🎯 Final result: {len(sources)} sources, {len(source_contents)} with content")
                    
        return sources, source_contents
    
    def query(self, user_query):
        """Process a user query - exact replica of reference app logic"""
        try:
            # Search for relevant documents with the sanitized query
            # (sanitization happens in the retriever's overridden search method)
            retriever_results = self.retriever.search(query_text=user_query)
            
            # Extract text from search results for context - exact logic
            context = ""
            if hasattr(retriever_results, "items") and retriever_results.items:
                for item in retriever_results.items:
                    if hasattr(item, "content"):
                        context += str(item.content) + "\n\n"
            
            # Extract sources and their content - exact logic
            sources, source_contents = self._extract_sources(retriever_results)
            
            # If we got no context or sources, it could be due to problematic characters
            if not context.strip() and not sources:
                # Try with a simplified query (keep only alphanumeric and spaces)
                simplified_query = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in user_query)
                simplified_query = ' '.join(simplified_query.split())
                
                # Only try again if the simplified query is significantly different and not empty
                if simplified_query.strip() and simplified_query != user_query:
                    print(f"Retrying with simplified query: '{simplified_query}'")
                    retriever_results = self.retriever.search(query_text=simplified_query)
                    
                    # Extract context again
                    context = ""
                    if hasattr(retriever_results, "items") and retriever_results.items:
                        for item in retriever_results.items:
                            if hasattr(item, "content"):
                                context += str(item.content) + "\n\n"
                    
                    # Extract sources again
                    sources, source_contents = self._extract_sources(retriever_results)
            
            # Create the RAG prompt - exact template from reference
            RAG_TEMPLATE = '''Answer the Question using the following Context. Only respond with information mentioned in the Context. Do not inject any speculative information not mentioned.

# Question:
{query_text}

# Context:
{context}

# Answer:
'''
            
            full_prompt = RAG_TEMPLATE.format(
                query_text=user_query,
                context=context
            )
            
            # Generate answer - always use RAG only, no history mixing
            answer = self._generate_completion(full_prompt, use_history=False)
            
        except Exception as e:
            print(f"Error in query processing: {e}")
            answer = f"I'm sorry, I encountered an error when processing your query. Please try a different question without special characters. Technical details: {str(e)}"
            sources = []
            source_contents = {}
        
        return {
            "query": user_query,
            "answer": answer,
            "sources": sources,
            "source_contents": source_contents
        }


# Exact replica of the reference app's DocumentRetriever
class ReferenceDocumentRetriever:
    def __init__(self, driver, embedder, retriever_type="hybrid"):
        """Initialize the document retriever - exact replica"""
        self.driver = driver
        self.embedder = embedder
        self.retriever_type = retriever_type
        self.retriever = self._create_retriever()
        
        # Override the search method of the retriever object to implement our sanitization
        original_search = self.retriever.search
        
        def safe_search(query_text, **kwargs):
            sanitized_query = self._sanitize_query(query_text)
            print(f"Original query: '{query_text}', Sanitized query: '{sanitized_query}'")
            try:
                return original_search(query_text=sanitized_query, **kwargs)
            except Exception as e:
                print(f"Error in retriever search: {str(e)}")
                # Return empty results on error
                try:
                    from neo4j_graphrag.models import RetrieverResult
                    return RetrieverResult(items=[])
                except:
                    # Fallback if RetrieverResult import fails
                    class EmptyResult:
                        def __init__(self):
                            self.items = []
                    return EmptyResult()
                
        # Replace the original search method with our sanitized version
        self.retriever.search = safe_search
        
    def _sanitize_query(self, query_text):
        """Sanitize the query text to handle special characters - exact replica"""
        if not query_text:
            return ""
            
        # Handle Lucene/Neo4j special characters that could cause issues in full-text search
        # These include: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
        special_chars = ['+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', 
                         '^', '"', '~', '*', '?', ':', '\\', '/']
        
        sanitized_query = query_text
        
        # Replace special characters with spaces
        for char in special_chars:
            sanitized_query = sanitized_query.replace(char, ' ')
        
        # Remove multiple spaces
        sanitized_query = ' '.join(sanitized_query.split())
        
        # Ensure no empty string which can cause issues
        if not sanitized_query.strip():
            sanitized_query = "retrievecontentemptyquery"
            
        return sanitized_query
        
    def _create_retriever(self):
        """Create the appropriate retriever based on the type - exact replica"""
        from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever, HybridCypherRetriever
        
        VECTOR_INDEX_NAME = "text_embeddings"
        
        if self.retriever_type == "vector":
            return VectorRetriever(
                self.driver,
                index_name=VECTOR_INDEX_NAME,
                embedder=self.embedder,
                return_properties=["text", "source2"]
            )
        elif self.retriever_type == "vector_cypher":
            return VectorCypherRetriever(
                self.driver,
                index_name=VECTOR_INDEX_NAME,
                embedder=self.embedder,
                retrieval_query=self._get_cypher_query()
            )
        elif self.retriever_type == "hybrid":
            return HybridCypherRetriever(
                self.driver, 
                vector_index_name=VECTOR_INDEX_NAME,
                fulltext_index_name=f"{VECTOR_INDEX_NAME}2", 
                retrieval_query=self._get_cypher_query(), 
                embedder=self.embedder
            )
        else:
            raise ValueError(f"Invalid retriever type: {self.retriever_type}")
            
    def _get_cypher_query(self):
        """Get the Cypher query for the retriever - simplified without APOC dependency"""
        return """
        // 1) Go out 2-3 hops in the entity graph and get relationships
        WITH node AS chunk
        MATCH (chunk)<-[:FROM_CHUNK]-()-[relList:!FROM_CHUNK]-{1,2}() 
        UNWIND relList AS rel

        // 2) Collect relationships, text chunks, and sources
        WITH collect(DISTINCT chunk)[0..10] AS chunks, 
          collect(DISTINCT rel)[0..20] AS rels

        // 3) Build concatenated strings manually without APOC
        UNWIND chunks AS c
        WITH collect(c.text) AS chunk_texts, collect(c.source2) AS chunk_sources, rels
        
        UNWIND rels AS r
        WITH chunk_texts, chunk_sources, 
             collect(startNode(r).name + ' - ' + type(r) + '(' + coalesce(r.details, '') + ')' + ' -> ' + endNode(r).name) AS rel_texts
        
        // Use reduce to concatenate instead of apoc.text.join
        RETURN 
          reduce(s = '', t IN chunk_texts | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + substring(t, 0, 1000)) AS truncated_chunk_texts,
          reduce(s = '', t IN chunk_sources | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + t) AS chunk_sources,
          reduce(s = '', t IN rel_texts | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + t) AS truncated_relationship_texts
        """


# Main RAG Pipeline that exactly replicates the reference app
class ReferenceRagPipeline:
    """RAG Pipeline that exactly replicates the reference Streamlit app"""
    
    def __init__(self):
        self.rag_enabled = False
        try:
            print("Initializing Reference RAG pipeline...")
            self.embedder = get_embedder()
            
            # Test Neo4j connection
            with Neo4jManager() as neo4j_manager:
                if not neo4j_manager.driver:
                    raise Exception("Failed to connect to Neo4j")
                result = neo4j_manager.driver.verify_connectivity()
                print(f"Neo4j connection verified: {result}")
                self.rag_enabled = True
                
            print("Reference RAG pipeline successfully initialized")
            
        except Exception as e:
            print(f"Error initializing Reference RAG pipeline: {str(e)}")
            self.rag_enabled = False
    
    def search(self, query: str, conversation_history=None, retriever_type=None, use_rag_format: bool = False) -> Dict[str, Any]:
        """Search using exact reference app logic"""
        print(f"Reference RAG search for query: {query}")
        
        if not self.rag_enabled:
            print("Reference RAG pipeline is not enabled")
            return {
                "answer": "I don't have enough evidence in the current knowledge base to answer.",
                "sources": []
            }
            
        try:
            # Create Neo4j connection
            with Neo4jManager() as neo4j_manager:
                # Create the retriever - use vector only to avoid APOC dependency
                retriever = ReferenceDocumentRetriever(
                    driver=neo4j_manager.driver,
                    embedder=self.embedder,
                    retriever_type="vector"  # Force vector to avoid APOC issues
                )
                
                # Create the LLM handler - exact replica
                llm_handler = ReferenceLLMHandler(retriever=retriever.retriever)
                
                # Process the query - exact replica
                result = llm_handler.query(query)
                
                print(f"Reference query result: {result['answer'][:100]}... with {len(result['sources'])} sources")
                
                return {
                    "answer": result["answer"],
                    "sources": result["sources"][:5],  # Limit to 5 sources like reference
                    "source_contents": result["source_contents"]
                }
                
        except Exception as e:
            print(f"Error during Reference RAG search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": "I don't have enough evidence in the current knowledge base to answer.",
                "sources": []
            }
