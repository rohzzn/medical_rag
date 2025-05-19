import React, { useState, useEffect } from 'react';

// Sources data for the modal
// This is a subset of the data from the old Streamlit app's components/sources.py
const SOURCE_URL_MAPPING: Record<string, string> = {
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
  'Close follow‐up is associated with fewer stricture formation.pdf': 'https://rdcrn.app.box.com/file/1806944286556',
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
  'Epithelial HIF-1α claudin-1 axis regulates barrier.pdf': 'https://rdcrn.app.box.com/file/1806947080578',
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
  'Mucosal Microbiota Associated With Eosinophilic.pdf': 'https://rdcrn.app.box.com/file/1806948193919'
};

interface AllSourcesModalProps {
  onClose: () => void;
}

const AllSourcesModal: React.FC<AllSourcesModalProps> = ({ onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortedSources, setSortedSources] = useState<Array<{ title: string; url: string }>>([]);
  
  // Process source data on component mount
  useEffect(() => {
    // Format and sort sources
    const sources = Object.entries(SOURCE_URL_MAPPING).map(([filename, url]) => {
      // Clean up the filename for display
      let title = filename.replace('.pdf', '');
      title = title.replace(/_/g, ' ');
      title = title.replace(/\(\d+\)/, ''); // Remove trailing numbers in parentheses
      
      return { title, url };
    });
    
    // Sort alphabetically
    const sorted = sources.sort((a, b) => 
      a.title.toLowerCase().localeCompare(b.title.toLowerCase())
    );
    
    setSortedSources(sorted);
  }, []);
  
  // Filter sources based on search term
  const filteredSources = sortedSources.filter(source => 
    searchTerm ? source.title.toLowerCase().includes(searchTerm.toLowerCase()) : true
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">All Source Documents</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-4 border-b border-gray-200">
          <input
            type="text"
            placeholder="Search sources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {filteredSources.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No sources found</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredSources.map((source, index) => (
                <a
                  key={index}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 border border-gray-200 rounded-md hover:bg-gray-50 truncate"
                >
                  <div className="flex items-start">
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" 
                      viewBox="0 0 20 20" 
                      fill="currentColor"
                    >
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                    </svg>
                    <span className="text-indigo-600 hover:text-indigo-800 truncate">{source.title}</span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-200 bg-gray-50 text-right">
          <button
            onClick={onClose}
            className="bg-gray-300 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-400"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AllSourcesModal; 