# Sales Leakage Detection & Revenue Opportunity Analytics
## Web Scraping + Hadoop HDFS + Data Mining + Streamlit Dashboard

This academic demo project combines:
1. Web scraping from the practice website Books to Scrape.
2. CSV datasets and simulated sales fields for demonstration.
3. Hadoop HDFS storage commands.
4. Data mining using Z-score and Isolation Forest.
5. An interactive Streamlit dashboard.

IMPORTANT: the website provides product information only. Units sold, cost, discount, region and sales values are simulated for coursework; they are not actual sales records.

## Requirements
- Python 3.10+
- Internet connection for scraping (optional if using included sample CSV)
- Hadoop 3.x configured in Ubuntu if you want to demonstrate HDFS
- A Windows or Ubuntu browser for Streamlit

## Setup in Ubuntu
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv unzip -y
cd ~/Downloads
unzip sales_leakage_streamlit_project.zip
cd sales_leakage_streamlit_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you already extracted the folder elsewhere, `cd` to that folder instead.

## Run the local data pipeline
```bash
python src/scrape_products.py
python src/create_sales_dataset.py
python src/analyze_leakage.py
```
The scraper may need internet access. If it fails, the included sample `data/scraped_products.csv` allows the other stages to run.

## Run the Streamlit dashboard
From the project root, with `.venv` activated:
```bash
streamlit run streamlit_app.py
```
Streamlit normally opens a browser automatically. If not, open the local URL printed in the terminal, usually `http://localhost:8501`.

The dashboard loads `output/leakage_results.csv` first, then `data/simulated_sales.csv`, then the sample data if present. It supports filters, KPI cards, charts, and a ranked priority table.

## HDFS storage (optional; run in Ubuntu where Hadoop is configured)
```bash
start-dfs.sh
jps
hdfs dfs -mkdir -p /sales-leakage/raw
hdfs dfs -mkdir -p /sales-leakage/processed
hdfs dfs -put -f data/scraped_products.csv /sales-leakage/raw/
hdfs dfs -put -f data/simulated_sales.csv /sales-leakage/processed/
hdfs dfs -put -f output/leakage_results.csv /sales-leakage/processed/
hdfs dfs -ls -R /sales-leakage
hdfs dfs -cat /sales-leakage/processed/leakage_results.csv | head
```
If you need to refresh the dashboard after running the pipeline, stop and rerun the app or use the dashboard's Refresh data button.

## Main files
- `src/scrape_products.py` — scrape product names, prices and URLs.
- `src/create_sales_dataset.py` — add simulated demonstration sales fields.
- `src/analyze_leakage.py` — calculate anomaly flags, scores, explanations and estimated recovery.
- `streamlit_app.py` — interactive dashboard.
- `hdfs_commands.txt` — commands for HDFS storage.
- `data/` and `output/` — datasets and analysis results.
