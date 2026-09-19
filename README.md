# super_twin

AI Digital Twin — a full-stack example that combines a FastAPI (Python) backend with a Next.js frontend to run a "digital twin" conversational assistant powered by LLMs. The repo includes local and S3-backed memory, SSE streaming endpoints, and Terraform for infra.

---

## Highlights

- FastAPI backend serving both standard JSON and Server-Sent Events (SSE) streaming endpoints
- Next.js (React) frontend with streaming UI that consumes SSE using `fetchEventSource`
- Conversation memory saved locally or to S3
- Example Terraform configuration for hosting static frontend artifacts and related infra
- Helper utilities for packaging / lambda-style deployments in `backend/lambda-package`

---

## Repo layout

- `backend/` — Python backend and API
  - `server.py` — main FastAPI app (SSE and REST endpoints)
  - `lambda-package/` — alternate server package for Lambda use
  - `models/`, `utils.py`, other supporting modules
  - `requirements.txt` / `pyproject.toml`
- `frontend/` — Next.js app
  - React components in `app/` and `components/` (chat UI, streaming handlers)
  - `package.json`, `next.config.ts`
- `terraform/` — Terraform configuration for cloud resources
- `memory/` — (local) conversation JSON files used in dev
- `scripts/` — deploy helper scripts

---

## Quickstart (dev)

Prereqs:
- Node.js (16+)
- Python 3.10+/3.11+ (the repo uses modern Python)
- `pip` and virtualenv/venv
- Terraform & AWS CLI (if using infra)

Backend (local):

```bash
# from repo root
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# run locally
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

The backend exposes endpoints such as:
- `GET /greeting` — non-streamed greeting
- `GET /greeting/stream` — SSE streaming greeting
- `POST /chat` — chat (also implemented as SSE streaming)
- `GET /conversation/{session_id}` — fetch saved conversation

Frontend:

```bash
cd frontend
npm install
npm run dev
# then open http://localhost:3000
```

Build and export static site (for S3 deployment):

```bash
cd frontend
npm run build
# if you use `next export` in package.json, run that to produce an `out/` folder
npm run export
# upload the `out/` folder to S3 or use the included deploy scripts
```

The frontend communicates with the backend using `NEXT_PUBLIC_API_URL` env var (see env below).

---

## Environment variables

Backend (example `.env` values):

```
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
USE_S3=false
S3_BUCKET=your-bucket-name
MEMORY_DIR=./memory
LLM_MODEL_ID=openai.gpt-oss-120b
AWS_BEDROCK_BASE_URL=...
PROJECT_ID=...
```

Frontend:
- `NEXT_PUBLIC_API_URL` — base URL for the backend API (used by client to call `/chat`, `/greeting/stream`, etc.)

Populate these env vars before running locally or in CI.

---

## Streaming (SSE) details

The project uses SSE for token-by-token streaming from the model:
- Backend streams events on `/greeting/stream` and `POST /chat` (SSE).
- Frontend consumes streams using `@microsoft/fetch-event-source` (`fetchEventSource`) and registers handlers for `onopen`, `onmessage`, `onclose`, and `onerror`.

Client behavior used in the app:
- `onopen` — push an empty `assistant` message into the UI to begin streaming
- `onmessage` — parse the SSE JSON chunk, append the `response` delta to the last assistant message
- `onclose`/`onerror` — finalize UI state and show errors if needed

This pattern keeps the chat UI responsive while the model generates text.

---

## Terraform & Deployment

There is a `terraform/` folder with infra snippets. Typical flow to deploy static frontend to S3 and configure DNS via Route 53 (example):

```bash
cd terraform
terraform init
terraform apply -var-file=terraform.tfvars -var="environment=dev"
```

Notes:
- When creating a Route 53 alias to an S3 website endpoint, you must use the region-specific S3 website Hosted Zone ID (AWS provides a static list). The repo includes notes/examples for mapping region → zone id.
- For HTTPS and better CDN behavior, prefer CloudFront in front of the S3 bucket and use ACM for certificates.

A simple manual deploy used in the repo:

```bash
# build & export from frontend, then upload to S3 bucket
cd frontend
npm run build && npm run export
aws s3 sync ./out s3://<your-bucket>
```

There are helper scripts in `scripts/` to automate common steps — inspect them for project-specific flows.

---

## Packaging / Lambda

The `backend/lambda-package` directory contains a packaged variant of the backend suitable for AWS Lambda or other function runtimes. See that folder for packaging steps and entrypoint differences.

---

## Tests & Linting

This repo does not currently include a formal test suite. Add unit tests for backend endpoints and React component tests as needed (Jest/React Testing Library for frontend; pytest for backend).

---

## Contributing

Contributions welcome. Suggested workflow:
1. Fork the repo
2. Create a feature branch
3. Run linters and basic manual tests locally
4. Open a PR with a clear description of changes and any migration steps

---

## Useful files

- `backend/server.py` — main FastAPI app
- `backend/lambda-package/server.py` — lambda-packaged variant
- `frontend/components/twin.tsx` — main chat UI + SSE handling
- `terraform/` — infrastructure-as-code

---

## License

Add a LICENSE file as appropriate for your project. This README does not add any license by itself.

---

If you'd like, I can:
- Add badges for CI / license / version
- Add a short quick demo GIF or screenshots to the README
- Create a CONTRIBUTING.md and ISSUE_TEMPLATE

