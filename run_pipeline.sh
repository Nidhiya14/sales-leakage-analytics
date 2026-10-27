#!/usr/bin/env bash
set -e
python src/scrape_products.py
python src/create_sales_dataset.py
python src/analyze_leakage.py
streamlit run streamlit_app.py
