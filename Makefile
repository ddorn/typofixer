run:
	uv run streamlit run --server.port 9113 typos_web/main.py


deploy:
	ssh pine 'cd /srv/typofixer && git pull && systemctl restart typofixer'
