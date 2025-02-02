run:
	uv run streamlit run --server.port 9113 typos_web/main.py


deploy:
	git ls-files | rsync -av --files-from=- . pine:/srv/typofixer
