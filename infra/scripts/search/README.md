# IRIS Symphony OSHA - Search Index Setup

## Overview
This script sets up Azure AI Search with OSHA recordkeeping knowledge files for RAG (Retrieval Augmented Generation) grounding.

## Knowledge Files
The search index is populated with OSHA regulatory knowledge files:
- `osha_1904_7_general_criteria.md` - Core recordability triggers
- `osha_1904_7_first_aid.md` - First aid vs medical treatment
- `osha_forms_300a.md` - Annual summary & posting requirements
- `osha_1904_5_work_relatedness.md` - Work-related determination
- `osha_1904_7_days_away.md` - Days away counting rules
- `osha_1904_29_privacy_cases.md` - Privacy concern cases
- `osha_1904_39_reporting.md` - Severe injury reporting (8hr/24hr)
- `osha_1904_41_electronic.md` - ITA electronic submission

## Environment Variables
```bash
# Azure OpenAI
AOAI_ENDPOINT=<aoai-endpoint>
EMBEDDING_DEPLOYMENT_NAME=<embedding-deployment-name>
EMBEDDING_MODEL_NAME=text-embedding-3-large
EMBEDDING_MODEL_DIMENSIONS=3072

# Storage
STORAGE_ACCOUNT_CONNECTION_STRING=<storage-connection-string>
BLOB_CONTAINER_NAME=osha-knowledge-files

# Search
SEARCH_ENDPOINT=<search-endpoint>
SEARCH_INDEX_NAME=sagevia-osha-knowledge-idx
```

## Running Setup (local)
```bash
az login
bash run_search_setup.sh <storage-account-name> <blob-container-name>
```

## Index Schema
The search index contains:
| Field | Type | Description |
|-------|------|-------------|
| `parent_id` | String | Source document ID |
| `title` | String | File name (e.g., `osha_1904_7_general_criteria.md`) |
| `chunk_id` | String | Unique chunk identifier (key) |
| `chunk` | String | Text content of the chunk |
| `text_vector` | Vector (3072) | Embedding for semantic search |

## Chunking Configuration
- **Split mode**: Pages
- **Maximum page length**: 2000 characters
- **Page overlap**: 500 characters

This ensures regulatory sections maintain context across chunk boundaries.

## Integration with IRIS Symphony
The search index serves as the RAG fallback layer:
```
User Query
    │
    ├─→ CLU (intent) → High confidence → Direct handler
    ├─→ CQA (FAQ) → Exact match → Pre-written answer
    └─→ FALLBACK → Search Index → GPT-grounded response
```

When CLU/CQA confidence is low, the system searches this index and uses retrieved chunks to ground GPT responses with accurate regulatory information.
