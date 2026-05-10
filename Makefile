.PHONY: install install-dev test lint run-gradio run-streamlit sync-space sync-space-dry

install:
	python -m pip install -U pip
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check src tests app.py app/streamlit_app.py

run-gradio:
	python app.py

run-streamlit:
	streamlit run app/streamlit_app.py

sync-space:
	./scripts/sync_hf_space.sh

sync-space-dry:
	./scripts/sync_hf_space.sh --dry-run
