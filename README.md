# BankBot_AI

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

BankBot_AI is a modular, production-oriented conversational assistant tailored to banking use-cases. It couples a compact NLU engine with a modular dialogue manager and a Streamlit demo UI to accelerate prototyping and early-stage deployments.

---

**Contents**

- Project overview
- Highlights
- Quick start
- Architecture & components
- Data, models & security
- Development & testing
- Deployment & CI recommendations
- Contributing & governance
- License & contact

## Project overview

This repository implements a clear separation between NLU, dialogue orchestration, and persistence. It is intended as a practical foundation for building banking assistants that can evolve from local demos to production services.

## Highlights

- Extensible intent and entity definitions with training utilities.
- Modular dialogue manager for deterministic and scripted flows.
- Streamlit demo providing a fast feedback loop for product stakeholders.
- Sample scripts for initializing demo data and local testing.

## Quick start

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the Streamlit demo:

```powershell
streamlit run streamlit_app.py
```

3. Run the main application (if desired):

```powershell
python main.py
```

## Architecture & components

- `nlu_engine/` — intent and entity definitions, training and inference helpers.
- `dialogue_manager/` — conversation state, handlers and flow orchestration.
- `database/` — DB utilities, CRUD helpers, `init_sample_data.py` for demos.
- `streamlit_app.py` / `app.py` — demo and alternate entry points.
- `models/` — local model artifacts (kept out of Git by `.gitignore`).

The codebase is designed so you can replace or augment components with external services (managed NLU, model endpoints, cloud DB) without changing the dialogue logic.

## Data, models & security

- Keep secrets (API keys, DB credentials) in a `.env` file and never commit them.
- Do not commit large model files. Use cloud storage or release attachments for sharing.
- For production, use TLS, managed secrets, and least-privilege database credentials.

Initialize demo data:

```powershell
python database/init_sample_data.py
```

## Development & testing

- Format code with `black` and lint with `ruff`/`flake8`.
- Add unit tests and run them with `pytest`.

Run tests:

```powershell
pytest -q
```

## Deployment & CI recommendations

- Add a `Dockerfile` for containerized deployments (Python 3.11-slim recommended).
- Use GitHub Actions to run linting, tests, and build images on PRs.
- Serve models via dedicated model-serving infrastructure for scalability.

## Contributing & governance

Contributions are welcome. Suggested workflow:

1. Fork and create a feature branch.
2. Implement changes with tests and documentation.
3. Submit a pull request describing the change and rationale.

Consider adding `CONTRIBUTING.md` and a `CODE_OF_CONDUCT.md` for community projects.

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

Maintained by Monika


---

Would you like me to:

- add an `MIT` license file now,
- scaffold `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`, or
- create a minimal `Dockerfile` and a GitHub Actions workflow template?

