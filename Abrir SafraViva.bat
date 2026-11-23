@echo off
rem Abre o painel SafraViva. No celular (mesmo Wi-Fi), use o endereco "Network URL" mostrado abaixo.
cd /d "%~dp0"
.venv\Scripts\python.exe -m scripts.rodar_etl --fontes previsao
.venv\Scripts\python.exe -m streamlit run app\main.py
