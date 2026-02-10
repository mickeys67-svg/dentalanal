@echo off
echo Deploying Dental Analyst Frontend to Google Cloud Run...
powershell -ExecutionPolicy ByPass -File .\manual_deploy_frontend.ps1
pause
