from custom_system.excel_parser import parse_machine_excel, save_config_json
from rag.embedding_store import EmbeddingStore
import logging
import os

logger = logging.getLogger("SentinelX.Ingestion")

def ingest_excel_system(excel_path):
    """
    Complete pipeline: Excel -> JSON Config -> FAISS RAG
    """
    logger.info(f"Starting ingestion for: {excel_path}")
    
    # 1. Parse Excel
    config = parse_machine_excel(excel_path)
    if not config:
        logger.error("Failed to parse Excel file.")
        return False
    
    # 2. Save JSON for dynamic thresholding
    save_config_json(config)
    
    # 3. Create RAG Documents
    docs = []
    docs.append(f"Machine Type: {config['machine_name']}")
    
    for sensor, details in config['sensors'].items():
        doc = f"Sensor {sensor}: Warning threshold is {details['warning']}{details['unit']}, " \
              f"Critical threshold is {details['critical']}{details['unit']}. {details['description']}"
        docs.append(doc)
    
    for rule in config['rules']:
        docs.append(f"Safety Rule: {rule}")
        
    for key, val in config['environment'].items():
        docs.append(f"Environment Setting {key}: {val}")
        
    # 4. Store in FAISS
    store = EmbeddingStore()
    store.add_documents(docs)
    
    logger.info("Ingestion complete. System reconfigured.")
    return True
