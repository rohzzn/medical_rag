import re
import json
from typing import List, Dict, Any, Optional
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.generation import RagTemplate
from neo4j_graphrag.generation.graphrag import GraphRAG

from app.rag.neo4j import Neo4jManager
from app.rag.embeddings import get_embedder
from app.rag.llm import get_llm
from app.schemas.query import Source


class RagPipeline:
    def __init__(self):
        self.embedder = get_embedder()
        self.llm = get_llm()
        
        # Define retrieval query for HybridCypherRetriever
        self.retrieval_query = """
        // 1) Go out 2-3 hops in the entity graph and get relationships
        WITH node AS chunk
        MATCH (chunk)<-[:FROM_CHUNK]-()-[relList:!FROM_CHUNK]-{1,2}() 
        UNWIND relList AS rel

        // 2) Collect relationships, text chunks, and sources
        WITH collect(DISTINCT chunk) AS chunks, 
          collect(DISTINCT rel) AS rels

        // 3) Format and return context with sources
        RETURN 
          substring(apoc.text.join([c in chunks | c.text], '\\n---\\n'), 0, 10000000) AS truncated_chunk_texts,
          substring(apoc.text.join([c in chunks | c.source2], '\\n---\\n'), 0, 10000000) AS chunk_sources,
          substring(apoc.text.join([r in rels | startNode(r).name + ' - ' + type(r) + '(' + coalesce(r.details, '') + ')' + ' -> ' + endNode(r).name], '\\n---\\n'), 0, 100000) AS truncated_relationship_texts
        """
        
        # Define prompt template
        self.rag_template = RagTemplate(
            template='''Answer the Question using the following Context. Only respond with information mentioned in the Context. Do not inject any speculative information not mentioned.

# Question:
{query_text}

# Context:
{context}

# Answer:
''', 
            expected_inputs=['query_text', 'context']
        )
    
    def _format_history(self, messages):
        """Format conversation history into a string."""
        formatted = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in messages])
        return formatted
    
    def _extract_sources(self, retriever_content: str) -> List[Source]:
        """Extract source documents from retriever content."""
        pattern = r"chunk_sources='(.*?)'(?=\s*truncated_relationship_texts=)"
        match = re.search(pattern, retriever_content, re.DOTALL)
        
        sources = []
        if match:
            chunk_sources_text = match.group(1)
            source_paths = re.split(r'\\n---\\n', chunk_sources_text)
            
            # Create unique sources
            unique_paths = set()
            for path in source_paths:
                path = path.strip()
                if path and path not in unique_paths:
                    unique_paths.add(path)
                    # Extract filename from path
                    source_name = path.split('\\')[-1] if '\\' in path else path.split('/')[-1]
                    sources.append(Source(source_path=path, source_name=source_name))
        
        return sources
    
    def search(self, query: str, conversation_history=None) -> Dict[str, Any]:
        """
        Search the knowledge graph and generate an answer with sources.
        
        Args:
            query: The user's query
            conversation_history: Optional list of previous messages
        
        Returns:
            Dict with answer and sources
        """
        with Neo4jManager() as neo4j_manager:
            # Create the hybrid cypher retriever
            hcretriever = HybridCypherRetriever(
                neo4j_manager.driver, 
                "text_embeddings",  # Vector index name
                "text_embeddings2",  # Fulltext index name
                self.retrieval_query, 
                self.embedder
            )
            
            # Create the GraphRAG instance
            h_rag = GraphRAG(
                llm=self.llm,
                retriever=hcretriever,
                prompt_template=self.rag_template
            )
            
            # Prepare the query with conversation history if provided
            if conversation_history:
                formatted_history = self._format_history(conversation_history)
                full_query = f"{formatted_history}\nuser: {query}"
            else:
                full_query = query
            
            # Get response from GraphRAG
            response = h_rag.search(full_query)
            
            # Get sources from retriever
            hc = hcretriever.search(query_text=full_query)
            sources = []
            for item in hc.items:
                item_sources = self._extract_sources(item.content)
                sources.extend(item_sources)
            
            # Make sure sources are unique
            unique_sources = []
            seen = set()
            for source in sources:
                if source.source_path not in seen:
                    seen.add(source.source_path)
                    unique_sources.append(source)
            
            return {
                "answer": response.answer,
                "sources": unique_sources
            }