# IRIS Symphony OSHA - Language Services Setup

## Overview
This folder contains scripts to set up Azure Language Services (CLU, CQA, Orchestration) and Azure AI Foundry Agents for OSHA recordkeeping assistance.

## Environment Variables
```bash
# Language Service
LANGUAGE_ENDPOINT=<language-service-endpoint>

# CLU (Intent Classification)
CLU_PROJECT_NAME=sagevia-osha-clu
CLU_MODEL_NAME=clu-m1
CLU_DEPLOYMENT_NAME=production

# CQA (Question Answering)
CQA_PROJECT_NAME=sagevia-osha-cqa
CQA_DEPLOYMENT_NAME=production

# Orchestration (CLU/CQA Router)
ORCHESTRATION_PROJECT_NAME=sagevia-osha-orchestration
ORCHESTRATION_MODEL_NAME=orch-m1
ORCHESTRATION_DEPLOYMENT_NAME=production

# AI Foundry Agents
AGENTS_PROJECT_ENDPOINT=<ai-foundry-project-endpoint>
AOAI_DEPLOYMENT=gpt-4o

# Translation
TRANSLATOR_RESOURCE_ID=<translator-resource-id>
TRANSLATOR_REGION=centralus
```

## Running Setup (local)
```bash
az login
source run_language_setup.sh
source run_agent_setup.sh
```

## OSHA Language Projects

### CLU Intents (6)
| Intent | Description |
|--------|-------------|
| RecordabilityQuestion | General recordability determination |
| FirstAidVsMedical | First aid vs medical treatment distinction |
| DaysAwayCalculation | Days away from work counting |
| IndustryRiskProfile | Industry risk data lookup |
| FormGeneration | OSHA form generation requests |
| DefinitionLookup | Regulatory definition queries |

### CLU Entities (4)
| Entity | Description |
|--------|-------------|
| InjuryType | Type of injury (laceration, fracture, etc.) |
| TreatmentType | Treatment provided (stitches, bandage, etc.) |
| NAICSCode | Industry classification code |
| FormType | OSHA form type (300, 300A, 301) |

### CQA Q&A Pairs (10)
Pre-written answers for common OSHA recordkeeping FAQs with CFR citations.

## IRIS Symphony Agents

### Agent Architecture
```
TranslationAgent (multilingual support)
       │
       ▼
  TriageAgent (CLU/CQA routing)
       │
       ▼
     Lumi (Primary Orchestrator)
       │
  ┌────┼────┐
  ▼    ▼    ▼
 ⚖️    📊    🤝
Gov   Ana   Exp
```

### Agents

| Agent | IRI Domain | Purpose | Zone APIs |
|-------|------------|---------|-----------|
| **Lumi** | Orchestrator | Routes to specialist agents | - |
| **GovernanceAgent** | ⚖️ Governance | Regulatory guidance | eCFR, Recordability |
| **AnalyticsAgent** | 📊 Analytics | Industry risk data | Analytics API |
| **ExperienceAgent** | 🤝 Experience | Incident management | Zone 2 (PII) |

### IRI Methodology
All agents follow Integrative Risk Intelligence principles:
- Present regulatory criteria, not conclusions
- Surface information from multiple domains
- Never make final determinations for users
- Cite authoritative sources (CFR sections, BLS data)

## Files

| File | Purpose |
|------|---------|
| `clu_setup.py` | Imports CLU project, trains and deploys model |
| `cqa_setup.py` | Creates CQA project, imports Q&A pairs, deploys |
| `orchestration_setup.py` | Links CLU/CQA into orchestration project |
| `agent_setup.py` | Creates AI Foundry agents (OSHA-customized) |
| `utils.py` | Shared utilities (credential, parameter binding) |
| `run_language_setup.sh` | Runs CLU/CQA/Orchestration setup |
| `run_agent_setup.sh` | Runs agent setup |

## Data Files (from `infra/data/`)
| File | Purpose |
|------|---------|
| `clu_import.json` | OSHA intents, entities, utterances |
| `cqa_import.json` | OSHA Q&A pairs with CFR citations |
| `orchestration_import.json` | Project routing configuration |
