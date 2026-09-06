# BioSync — Hybrid ML/QML Health Risk Assessment

BioSync is a disease-specific, model-based risk-assessment workflow with separate patient and doctor views.

## Supported conditions
- Cardiovascular
- Diabetes

## Architecture
Browser → Next.js frontend → Express backend → MongoDB ↔ FastAPI ML API

## Repository structure
- `frontend/` — Next.js application
- `backend/` — Express/MongoDB API and authentication
- `ml-api/` — FastAPI inference service and ML/QML runtime
- `data/` — supplied datasets and evaluation splits

## Local setup
1. Start MongoDB.
2. Copy `backend/.env.example` to `backend/.env` and set a strong `SESSION_SECRET`.
3. Install backend dependencies and run the backend on port 4000.
4. Install frontend dependencies and run the Next.js app on port 3000.
5. Install `ml-api/requirements.txt` in a Python environment and run the FastAPI service on port 8000.

See `RUN_FIRST.md` and the component documentation for the detailed workflow.

## Safety / evidence framing
Positive/negative predictions are model class labels, not diagnoses. Model-derived percentages are not presented as clinically validated probabilities, and risk bands are product display bands rather than validated clinical thresholds. The project documents provenance limitations for reconstructed quantum artifacts.
