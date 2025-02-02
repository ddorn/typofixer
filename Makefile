# Set uv to either /root/.local/bin/uv or uv depending on which one exists
UV := $(shell command -v uv >/dev/null 2>&1 && echo "uv" || echo "/root/.local/bin/uv")

run:
	$(UV) run streamlit run --server.port 9113 typos_web/main.py


deploy:
	ssh pine 'cd /srv/typofixer && git pull && systemctl restart typofixer'
