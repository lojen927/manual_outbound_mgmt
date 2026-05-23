@echo off
cd /d "C:\Users\luo-j\VS Code\manual_outbound_mgmt"
".venv\Scripts\python.exe" manage.py export_daily --days=7
