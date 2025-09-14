import os
import re
import json
from typing import List, Dict, Any, Optional, Union
import neo4j
from neo4j_graphrag.generation import RagTemplate
from neo4j_graphrag.generation.graphrag import GraphRAG
from neo4j_graphrag.retrievers import HybridCypherRetriever, VectorCypherRetriever, VectorRetriever
try:
    from neo4j_graphrag.models import RetrieverResult as _RetrieverResult
except Exception:
    class _RetrieverResult:  # Fallback minimal implementation
        def __init__(self, items=None):
            self.items = items or []

RetrieverResult = _RetrieverResult

from app.rag.neo4j import Neo4jManager
from app.rag.embeddings import get_embedder
from app.rag.llm import get_llm
from app.rag.rag_assistant import format_rag_response
from app.rag.reference_rag import ReferenceRagPipeline
from app.schemas.query import Source, RagResponse
from app.core.config import settings


class RagPipeline:
    """
    RAG Pipeline that uses the exact reference app logic for consistent results.
    """
    def __init__(self):
        try:
            print("Initializing RAG pipeline using reference app logic...")
            
            # Use the reference implementation
            self.reference_pipeline = ReferenceRagPipeline()
            self.rag_enabled = self.reference_pipeline.rag_enabled
                
            print("RAG pipeline successfully initialized using reference app logic")
            
        except Exception as e:
            print(f"Error initializing RAG pipeline: {str(e)}")
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
                                paper_url=box_url,
                                location="From knowledge graph",
                                why_it_supports="Contains relevant medical information about the topic in the query."
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
                            paper_url=box_url,
                            location="From knowledge graph",
                            why_it_supports="Contains relevant medical information about the topic in the query."
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
    
    def search(self, query: str, conversation_history=None, retriever_type=None, use_rag_format: bool = False) -> Union[Dict[str, Any], RagResponse]:
        """
        Search using the exact reference app logic for consistent results.
        """
        print(f"RAG search for query: {query} with retriever type: {retriever_type or 'hybrid'}")
        
        if not self.rag_enabled:
            print("RAG pipeline is not enabled")
            error_message = "I don't have enough evidence in the current knowledge base to answer."
            
            if use_rag_format:
                return RagResponse(answer=error_message, sources=[])
            else:
                return {
                    "answer": error_message,
                    "sources": []
                }
        
        # Delegate to the reference pipeline for consistent results
        result = self.reference_pipeline.search(
            query=query,
            conversation_history=conversation_history,
            retriever_type=retriever_type,
            use_rag_format=use_rag_format
        )
        
        # Convert sources to Source objects for compatibility
        if "sources" in result and isinstance(result["sources"], list):
            converted_sources = []
            source_contents = result.get("source_contents", {})
            
            for source_path in result["sources"]:
                source_name = source_path.split('\\')[-1] if '\\' in source_path else source_path.split('/')[-1]
                clean_name = self._clean_source_name(source_name)
                url = self._get_box_url(source_name)
                content = source_contents.get(source_path, "")
                
                src_obj = Source(
                    source_path=source_path,
                    source_name=clean_name,
                    paper_url=url,
                    content=content[:1000] if content else "",
                    location="Document excerpt",
                    why_it_supports="Contains relevant information that directly addresses the query."
                )
                converted_sources.append(src_obj)
            
            result["sources"] = converted_sources
        
        if use_rag_format:
            # Convert to RagResponse format if needed
            from app.rag.rag_assistant import format_rag_response
            # Create dummy items for format_rag_response
            items = []
            for source_path in result.get("sources", []):
                if hasattr(source_path, 'source_path'):
                    source_path = source_path.source_path
                class DummyItem:
                    def __init__(self, path, content):
                        self.content = f"chunk_sources='{path}' truncated_chunk_texts='{content}'"
                content = result.get("source_contents", {}).get(source_path, "")
                items.append(DummyItem(source_path, content))
            
            return format_rag_response(result["answer"], items, retriever_type or "hybrid")
        
        return result

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