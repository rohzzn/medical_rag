import os
import re
import json
from typing import List, Dict, Any, Optional
import neo4j
from neo4j_graphrag.generation import RagTemplate
from neo4j_graphrag.generation.graphrag import GraphRAG
from neo4j_graphrag.retrievers import HybridCypherRetriever, VectorCypherRetriever, VectorRetriever

from app.rag.neo4j import Neo4jManager
from app.rag.embeddings import get_embedder
from app.rag.llm import get_llm
from app.schemas.query import Source


class RagPipeline:
    """
    RAG Pipeline implementation that closely follows the Jupyter notebook implementation.
    """
    def __init__(self):
        try:
            print("Initializing RAG pipeline following Jupyter notebook approach...")
            
            # Initialize OpenAI LLM and embeddings
            self.embedder = get_embedder()
            self.llm = get_llm()
            
            # Set up retrieval query - significantly reduced limits to avoid token limit errors
            self.retrieval_query = """
            // 1) Go out 2-3 hops in the entity graph and get relationships
            WITH node AS chunk
            MATCH (chunk)<-[:FROM_CHUNK]-()-[relList:!FROM_CHUNK]-{1,2}() 
            UNWIND relList AS rel

            // 2) Collect relationships, text chunks, and sources
            WITH collect(DISTINCT chunk)[0..10] AS chunks, // Increased chunk limit for better coverage
              collect(DISTINCT rel)[0..20] AS rels // Increased relationship limit for better context

            // 3) Format and return context with sources
            UNWIND chunks AS c
            WITH collect(c.text) AS chunk_texts, collect(c.source2) AS chunk_sources, rels
            
            UNWIND rels AS r
            WITH chunk_texts, chunk_sources, collect(startNode(r).name + ' - ' + type(r) + '(' + coalesce(r.details, '') + ')' + ' -> ' + endNode(r).name)[0..20] AS rel_texts // Increased relationship texts
            
            RETURN 
              reduce(s = '', t IN chunk_texts | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + substring(t, 0, 1000)) AS truncated_chunk_texts, // Increased chunk size to 1000 chars
              reduce(s = '', t IN chunk_sources | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + t) AS chunk_sources,
              reduce(s = '', t IN rel_texts | s + CASE WHEN s = '' THEN '' ELSE '\n---\n' END + t) AS truncated_relationship_texts
            """
            
            # Set up RAG template - identical to notebook
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
            
            # Test Neo4j connection
            with Neo4jManager() as neo4j_manager:
                if not neo4j_manager.driver:
                    raise Exception("Failed to connect to Neo4j")
                result = neo4j_manager.driver.verify_connectivity()
                print(f"Neo4j connection verified: {result}")
                self.rag_enabled = True
                
            print("RAG pipeline successfully initialized matching Jupyter notebook")
            
        except Exception as e:
            print(f"Error initializing RAG pipeline (detailed): {str(e)}")
            self.rag_enabled = False
    
    def _format_history(self, messages):
        """Format conversation history into a string."""
        return "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in messages])
    
    def _extract_sources(self, retriever_content: str) -> List[Source]:
        """Extract source documents from retriever content."""
        sources = []
        try:
            # Debugging
            print(f"Content to extract sources from: {retriever_content[:200]}...")
            
            # Handle Neo4j Record format - first check if this is a Record
            if retriever_content.strip().startswith('<Record'):
                # Try to extract the chunk_sources directly
                source_match = re.search(r"chunk_sources='(.*?)'", retriever_content)
                if source_match:
                    print("Found sources in Record format")
                    chunk_sources_text = source_match.group(1)
                    source_paths = re.split(r'\\n---\\n', chunk_sources_text)
                    
                    # Add sources from the paths
                    for path in source_paths:
                        path = path.strip()
                        if path:
                            # Extract filename from path
                            source_name = path.split('\\')[-1] if '\\' in path else path.split('/')[-1]
                            
                            # Clean up the source name
                            clean_source_name = self._clean_source_name(source_name)
                            
                            # Get the Box URL for the source
                            box_url = self._get_box_url(source_name)
                            
                            sources.append(Source(
                                source_path=path, 
                                source_name=clean_source_name,
                                paper_url=box_url
                            ))
                            print(f"Added source: {clean_source_name}")
                    
                    return sources
            
            # If not Record format, use regex to extract chunk_sources - try multiple patterns
            source_patterns = [
                r"chunk_sources='(.*?)'(?=\s*truncated_relationship_texts=)",  # Original pattern
                r"chunk_sources[=:]'(.*?)'",  # Alternative pattern
                r"'chunk_sources':\s*'(.*?)'",  # JSON-like pattern
                r"chunk_sources\s*=\s*['\"](.*?)['\"]"  # Assignment pattern
            ]
            
            match = None
            for pattern in source_patterns:
                match = re.search(pattern, str(retriever_content), re.DOTALL)
                if match:
                    print(f"Found sources using pattern: {pattern}")
                    break
            
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
                        
                        # Clean up the source name
                        clean_source_name = self._clean_source_name(source_name)
                        
                        # Get the Box URL for the source
                        box_url = self._get_box_url(source_name)
                        
                        sources.append(Source(
                            source_path=path, 
                            source_name=clean_source_name,
                            paper_url=box_url
                        ))
                        print(f"Added source: {clean_source_name}")
                
                print(f"Extracted {len(sources)} sources")
            else:
                print("No sources found in content - couldn't match any source patterns")
        except Exception as e:
            print(f"Error extracting sources: {e}")
            import traceback
            traceback.print_exc()
        
        return sources
    
    def _get_retriever(self, neo4j_manager, retriever_type=None):
        """
        Create and return the appropriate retriever based on the specified type.
        
        Args:
            neo4j_manager: Neo4j connection manager
            retriever_type: Type of retriever to use (hybrid, vector_cypher, or vector)
            
        Returns:
            A configured retriever instance
        """
        # Get retriever type from environment or parameter, default to hybrid
        retriever_type = retriever_type or os.getenv("RETRIEVER_TYPE", "hybrid")
        print(f"Creating retriever of type: {retriever_type}")
        
        # Create appropriate retriever based on type
        if retriever_type == "vector":
            return VectorRetriever(
                neo4j_manager.driver,
                index_name="text_embeddings",
                embedder=self.embedder,
                return_properties=["text", "source2"]
            )
        elif retriever_type == "vector_cypher":
            return VectorCypherRetriever(
                neo4j_manager.driver, 
                index_name="text_embeddings",
                embedder=self.embedder,
                retrieval_query=self.retrieval_query
            )
        else:  # default to hybrid
            return HybridCypherRetriever(
                neo4j_manager.driver, 
                vector_index_name="text_embeddings",
                fulltext_index_name="text_embeddings2", 
                retrieval_query=self.retrieval_query, 
                embedder=self.embedder
            )
    
    def search(self, query: str, conversation_history=None, retriever_type=None) -> Dict[str, Any]:
        """
        Search the knowledge graph and generate an answer with sources.
        
        Args:
            query: The user's query
            conversation_history: Optional list of previous messages
            retriever_type: Optional retriever type to use (hybrid, vector_cypher, or vector)
        
        Returns:
            Dict with answer and sources
        """
        print(f"RAG search for query: {query} with retriever type: {retriever_type or os.getenv('RETRIEVER_TYPE', 'hybrid')}")
        
        if not self.rag_enabled:
            print("RAG pipeline is not enabled")
            return {
                "answer": "I'm sorry, but there was an issue connecting to the knowledge graph. Please check the Neo4j connection and OpenAI API key configuration.",
                "sources": []
            }
            
        try:
            # Create Neo4j connection
            with Neo4jManager() as neo4j_manager:
                # Create the appropriate retriever
                retriever = self._get_retriever(neo4j_manager, retriever_type)
                
                # Create the GraphRAG instance
                h_rag = GraphRAG(
                    llm=self.llm,
                    retriever=retriever,
                    prompt_template=self.rag_template
                )
                
                # Prepare the query with conversation history if provided
                if conversation_history and len(conversation_history) > 0:
                    formatted_history = self._format_history(conversation_history)
                    full_query = f"{formatted_history}\nuser: {query}"
                else:
                    full_query = query
                
                print(f"Full query: {full_query}")
                
                # Get response from GraphRAG
                response = h_rag.search(full_query)
                answer = response.answer
                
                # Get sources from retriever
                hc = retriever.search(query_text=full_query)
                sources = []
                
                # Add diagnostic output to understand what we're getting
                print(f"==== Retrieved {len(hc.items)} items from retriever ====")
                for i, item in enumerate(hc.items):
                    print(f"Item {i} type: {type(item)}")
                    if hasattr(item, 'content'):
                        print(f"Item {i} content type: {type(item.content)}")
                        print(f"Item {i} content preview: {str(item.content)[:300]}")
                    elif hasattr(item, 'text'):
                        print(f"Item {i} has text attribute: {item.text[:300]}")
                    else:
                        print(f"Item {i} attributes: {dir(item)}")
                
                for item in hc.items:
                    # Handle different retriever types differently
                    if isinstance(retriever, VectorRetriever):
                        try:
                            content = item.content
                            # Check if this is a Neo4j Record format
                            if isinstance(content, str) and content.strip().startswith('<Record'):
                                source_match = re.search(r"chunk_sources='(.*?)'", content)
                                if source_match:
                                    print("Found sources in Record format for Vector retriever")
                                    chunk_sources_text = source_match.group(1)
                                    source_paths = re.split(r'\\n---\\n', chunk_sources_text)
                                    
                                    # Add sources from the paths
                                    for path in source_paths:
                                        path = path.strip()
                                        if path:
                                            # Extract filename from path
                                            source_name = path.split('\\')[-1] if '\\' in path else path.split('/')[-1]
                                            
                                            # Clean up the source name
                                            clean_source_name = self._clean_source_name(source_name)
                                            
                                            # Get the Box URL for the source
                                            box_url = self._get_box_url(source_name)
                                            
                                            sources.append(Source(
                                                source_path=path, 
                                                source_name=clean_source_name,
                                                paper_url=box_url
                                            ))
                                            print(f"Added vector source: {clean_source_name}")
                            else:
                                print("No chunk_sources found in Record format")
                                try:
                                    # First attempt: parse as JSON
                                    data_dict = json.loads(content.replace("'", '"'))
                                    source = data_dict.get("source2", "")
                                except json.JSONDecodeError:
                                    # Second attempt: extract using regex
                                    source_match = re.search(r"source2'\s*:\s*'([^']+)'", str(content))
                                    source = source_match.group(1) if source_match else ""
                                    if not source:
                                        # Third attempt: extract from raw text
                                        source_match = re.search(r"source2[=:]\s*([^\s,}]+)", str(content))
                                        source = source_match.group(1) if source_match else ""
                                      
                                if source:
                                    source_name = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
                                    
                                    # Clean up the source name
                                    clean_source_name = self._clean_source_name(source_name)
                                    
                                    # Get the Box URL for the source
                                    box_url = self._get_box_url(source_name)
                                    
                                    sources.append(Source(
                                        source_path=source, 
                                        source_name=clean_source_name,
                                        paper_url=box_url
                                    ))
                                    print(f"Successfully extracted source: {clean_source_name}")
                        except Exception as e:
                            print(f"Error extracting source from vector retriever (with details): {e}, content type: {type(item.content)}")
                            print(f"Content preview: {str(item.content)[:100]}...")
                    else:
                        # For VectorCypherRetriever and HybridCypherRetriever
                    item_sources = self._extract_sources(item.content)
                    sources.extend(item_sources)
                
                # Make sure sources are unique
                unique_sources = []
                seen = set()
                for source in sources:
                    # Use source name for uniqueness check to avoid duplication
                    if source.source_name not in seen:
                        seen.add(source.source_name)
                        unique_sources.append(source)
                
                # Limit to top 5 sources
                unique_sources = unique_sources[:5]
                
                # Try to extract snippets from chunks for each source
                source_content = {}
                try:
                    for item in hc.items:
                        if hasattr(item, 'content') and 'truncated_chunk_texts' in str(item.content):
                            chunk_text = re.search(r"truncated_chunk_texts='(.*?)'", str(item.content), re.DOTALL)
                            if chunk_text:
                                chunks = re.split(r'\\n---\\n', chunk_text.group(1))
                                # Process up to 10 chunks for better information extraction
                                chunks = chunks[:10]
                                # First, prioritize chunks with keywords for important topics
                                prioritized_chunks = []
                                regular_chunks = []
                                
                                # Categorize chunks by relevance
                                for chunk in chunks:
                                    # Check for important keywords
                                    is_priority = any(keyword in chunk.lower() for keyword in 
                                                   ['fda-approved', 'fda approved', 'dupilumab', 'dupixent', 
                                                    'eoe1', 'eoe2', 'eoe3', 'eoee1', 'eoee2', 'eoee3',
                                                    'three endotypes', 'primary endotypes', 'il-13', 'il-4',
                                                    'pathogenesis'])
                                    if is_priority:
                                        prioritized_chunks.append(chunk)
                                    else:
                                        regular_chunks.append(chunk)
                                
                                # Combine prioritized chunks first, then regular chunks
                                processed_chunks = prioritized_chunks + regular_chunks
                                
                                for source in unique_sources:
                                    if source.source_path not in source_content:
                                        # Find chunks that might be from this source
                                        matching_chunks = []
                                        for chunk in processed_chunks:
                                            if len(matching_chunks) < 2:  # Limit to 2 chunks per source
                                                # Improved heuristic to match chunks to sources
                                                source_words = set(source.source_name.lower().replace('.pdf', '').replace('_', ' ').split())
                                                if any(word in chunk.lower() for word in source_words if len(word) > 3):
                                                    # Extract most relevant section of the chunk
                                                    chunk_extract = self._extract_relevant_section(chunk, source)
                                                    # Truncate chunk to maximum 500 characters
                                                    matching_chunks.append(chunk_extract[:500] + ("..." if len(chunk_extract) > 500 else ""))
                                        
                                        if matching_chunks:
                                            source_content[source.source_path] = "\n...\n".join(matching_chunks)
                except Exception as e:
                    print(f"Error extracting source content: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Attach content to sources
                for source in unique_sources:
                    if source.source_path in source_content:
                        source.content = source_content[source.source_path]
                    else:
                        source.content = "Content not available"
                
                print(f"Query result: {answer[:100]}... with {len(unique_sources)} sources")
                
                return {
                    "answer": answer,
                    "sources": unique_sources
                }
        except Exception as e:
            print(f"Error during RAG search: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": []
            }

    def _extract_relevant_section(self, chunk: str, source: Source) -> str:
        """Extract the most relevant section of a chunk for a particular source and topic."""
        # Clean up the chunk text by removing newlines and fixing spacing
        chunk = re.sub(r'\n', ' ', chunk)
        chunk = re.sub(r'\s+', ' ', chunk)
        chunk = chunk.strip()
        
        # Split the chunk into sentences
        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        if not sentences:
            return chunk
            
        # Look for key terms
        key_terms = {
            'FDA approval': ['fda', 'approved', 'approval', 'dupilumab', 'dupixent'],
            'endotypes': ['endotype', 'eoe1', 'eoe2', 'eoe3', 'eoee1', 'eoee2', 'eoee3'],
            'pathogenesis': ['pathogenesis', 'il-13', 'il-4', 'interleukin', 'inflammation']
        }
        
        # Score each sentence by relevance
        scored_sentences = []
        for sentence in sentences:
            score = 0
            lower_sentence = sentence.lower()
            
            # Score by key terms
            for category, terms in key_terms.items():
                if any(term in lower_sentence for term in terms):
                    score += 5
            
            # Score by source name terms
            source_words = set(source.source_name.lower().replace('.pdf', '').replace('_', ' ').split())
            for word in source_words:
                if len(word) > 3 and word in lower_sentence:
                    score += 2
                    
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:3]]  # Take top 3 sentences
        
        # Reconstruct text in original order
        original_order = []
        for sentence in sentences:
            if sentence in top_sentences:
                original_order.append(sentence)
                
        if not original_order:
            cleaned_text = chunk[:500]  # If no sentences were selected, return beginning of chunk
        else:
            cleaned_text = " ".join(original_order)
        
        # Final cleanup to ensure the text is well-formatted
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
        
    def _clean_source_name(self, source_name: str) -> str:
        """Clean up the source name by removing file extensions and formatting."""
        # Remove .pdf extension
        clean_name = source_name.replace('.pdf', '')
        
        # Replace underscores with spaces
        clean_name = clean_name.replace('_', ' ')
        
        # Handle special characters
        clean_name = clean_name.replace('â€', "'")
        
        return clean_name
    
    def _get_box_url(self, source_name: str) -> str:
        """Get the Box URL for a source if available."""
        # Check if the source name is in our mapping
        if source_name in self.SOURCE_URL_MAPPING:
            return self.SOURCE_URL_MAPPING[source_name]
        
        # Try to find a partial match
        for filename, url in self.SOURCE_URL_MAPPING.items():
            if source_name in filename or filename in source_name:
                return url
        
        # Fallback to Google Scholar search
        return f"https://scholar.google.com/scholar?q={source_name.replace('.pdf', '').replace('_', '+')}"

    # Map of source file names to their Box URLs
    SOURCE_URL_MAPPING = {
        'A Clinical Severity Index for Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806944500611',
        'A Comparative Analysis of Eating Behavior of School-Aged Children with Eosinophilic Esophagitis and Their Caregivers_ Quality of Life_ Perspectives of Caregivers.pdf': 'https://rdcrn.app.box.com/file/1806947473266',
        'A Deep Multi-Label Segmentation Network For Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806944461539',
        'A novel approach to conducting clinical trials in the community setting_ utilizing patient-driven platforms and social media to drive web-based patient recruitment.pdf': 'https://rdcrn.app.box.com/file/1806932521580',
        'Alignment of parent- and child-reported outcomes and histology in eosinophilic esophagitis across multiple CEGIR sites.pdf': 'https://rdcrn.app.box.com/file/1806930362344',
        'Allergic mechanisms of Eosinophilic oesophagitis.pdf': 'https://rdcrn.app.box.com/file/1806947471313',
        'Antifibrotic Effects of the Thiazolidinediones in Eosinophilic Esophagitis Pathologic Remodeling_ A Preclinical Evaluation.pdf': 'https://rdcrn.app.box.com/file/1806945829739',
        'Assessing Adherence and Barriers to Long-Term Elimination Diet Therapy in Adults with Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806946955778',
        'Association Between Endoscopic and Histologic Findings in a Multicenter Retrospective Cohort of Patients with Non-esophageal Eosinophilic Gastrointestinal Disorders.pdf': 'https://rdcrn.app.box.com/file/1806925663066',
        'Autophagy mediates epithelial cytoprotection in eosinophilic oesophagitis.pdf': 'https://rdcrn.app.box.com/file/1806945942226',
        'a_multicenter_long_term_cohort_study_of.2.pdf': 'https://rdcrn.app.box.com/file/1806947164012',
        'Benralizumab for eosinophilic gastritis a single-site,.pdf': 'https://rdcrn.app.box.com/file/1806946180452',
        'CD73D Epithelial Progenitor Cells That Contribute to.pdf': 'https://rdcrn.app.box.com/file/1806945011870',
        'Characterization of eosinophilic esophagitis variants by clinical,.pdf': 'https://rdcrn.app.box.com/file/1806945747887',
        'Close followâ€up is associated with fewer stricture formation.pdf': 'https://rdcrn.app.box.com/file/1806944286556',
        'Comorbid Diagnosis of Eosinophilic Esophagitis and.pdf': 'https://rdcrn.app.box.com/file/1806931506338',
        'Creating a multi-center rare disease consortium _ the Consortium of Eosinophilic Gastrointestinal Disease Researchers _CEGIR_.pdf': 'https://rdcrn.app.box.com/file/1806947265419',
        'Defining the Patchy Landscape of Esophageal Eosinophilia in.pdf': 'https://rdcrn.app.box.com/file/1806947901302',
        'Detergent exposure induces epithelial barrier dysfunction andeosinophilic inflammation in the esophagus.pdf': 'https://rdcrn.app.box.com/file/1806945582357',
        'Development and Validation of Web-based Tool to Predict.pdf': 'https://rdcrn.app.box.com/file/1806947631799',
        'Diagnosis of Pediatric Non-Esophageal Eosinophilic Gastrointestinal Disorders by Eosinophil Peroxidase Immunohistochemistry.pdf': 'https://rdcrn.app.box.com/file/1806943072770',
        'Dilation of Pediatric Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806945961514',
        'Direct-to-Consumer Recruitment Methods via Traditional and.pdf': 'https://rdcrn.app.box.com/file/1806946091847',
        'Early life factors are associated with risk for eosinophilic esophagitis diagnosed in adulthood.pdf': 'https://rdcrn.app.box.com/file/1806946576676',
        'Effects of allergen sensitization on response to therapy in children with eosinophilic esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806931077174',
        'Efficacy and safety of dupilumab up to 52 weeks in adults.pdf': 'https://rdcrn.app.box.com/file/1806944730328',
        'Eosinophil Knockout Humans Uncovering the Role of.pdf': 'https://rdcrn.app.box.com/file/1806947622671',
        'Eosinophilic Esophagitis Patients Are Not at.pdf': 'https://rdcrn.app.box.com/file/1806944246081',
        'Eosinophilic Esophagitis(2).pdf': 'https://rdcrn.app.box.com/file/1806930066958',
        'Eosinophilic Esophagitis_ Existing and Upcoming Therapies in an Age of Emerging Molecular and Personalized Medicine.pdf': 'https://rdcrn.app.box.com/file/1806947204812',
        'Eosinophilic oesophagitis endotype classification by molecular_ clinical_ and histopathological analyses_ a cross-sectional study.pdf': 'https://rdcrn.app.box.com/file/1806943710336',
        'Epithelial HIF-1Î± claudin-1 axis regulates barrier.pdf': 'https://rdcrn.app.box.com/file/1806947080578',
        'Epithelial origin of eosinophilic esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806946326713',
        'Esophageal Epithelium and Lamina Propria Are Unevenly.pdf': 'https://rdcrn.app.box.com/file/1806947872259',
        'Esophageal Manifestations of Dermatological Diseases,.pdf': 'https://rdcrn.app.box.com/file/1806943139759',
        'Evaluating Eosinophilic Colitis as a Unique Disease using.pdf': 'https://rdcrn.app.box.com/file/1806946849658',
        'Examining Disparities in Pediatric Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806930549544',
        'Food allergen triggers are increased in children with the TSLP risk allele and eosinophilic esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806947514476',
        'Genome-wide admixture and association analysis identifies African ancestry specific risk loci of eosinophilic esophagitis in African American.pdf': 'https://rdcrn.app.box.com/file/1806945388098',
        'Harnessing artificial intelligence to infer novel spatial biomarkers for the diagnosis of eosinophilic esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806943427237',
        'High Patient Disease Burden in a Cross_sectional_ Multicenter Contact Registry Study of Eosinophilic Gastrointestinal Diseases.pdf': 'https://rdcrn.app.box.com/file/1806928098293',
        'Histologic improvement after 6 weeks of dietary elimination for eosinophilic esophagitis may be insufficient to determine efficacy.pdf': 'https://rdcrn.app.box.com/file/1806943342990',
        'Histological Phenotyping in Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806930047667',
        'Human Epidemiology and RespOnse to SARS-CoV-2 (HEROS) Objectives, Design.pdf': 'https://rdcrn.app.box.com/file/1806947399443',
        'Impact of the COVID-19 Pandemic on People Living With Rare.pdf': 'https://rdcrn.app.box.com/file/1806946065334',
        'Impressions and Aspirations from the FDA GREAT VI Workshop.pdf': 'https://rdcrn.app.box.com/file/1806948152579',
        'Increasing Rates of Diagnosis, Substantial Co-occurrence, and.pdf': 'https://rdcrn.app.box.com/file/1806932519666',
        'Inflammation-associated microbiota in pediatric eosinophilic esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806943127793',
        'International Consensus Recommendations for Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806945364783',
        'Local type 2 immunity in eosinophilic gastritis.pdf': 'https://rdcrn.app.box.com/file/1806947457540',
        'Loss of Endothelial TSPAN12 Promotes Fibrostenotic.pdf': 'https://rdcrn.app.box.com/file/1806943242663',
        'Management of Esophageal Food Impaction Varies Among Gastroenterologists and Affects Identification of Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806947834259',
        'Mast Cell Infiltration Is Associated With Persistent Symptoms and Endoscopic Abnormalities Despite Resolution of Eosinophilia in Pediatric Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806946859533',
        'Molecular analysis of duodenal eosinophilia.pdf': 'https://rdcrn.app.box.com/file/1806947303831',
        'Motivations_ Barriers_ and Outcomes of Patient-Reported Shared Decision Making in Eosinophilic Esophagitis.pdf': 'https://rdcrn.app.box.com/file/1806946309943',
        'Mucosal Microbiota Associated With Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806948193919',
        'Scientific Journey to the First FDA-approved Drug for.pdf': 'https://rdcrn.app.box.com/file/1806947065648',
        'Pediatric Eosinophilic Esophagitis Endotypes_ Are We Closer to Predicting Treatment Response_.pdf': 'https://rdcrn.app.box.com/file/1806945174239',
            }