# PowerShell helper to run the Flask app safely
$python = "C:/Users/Darshan K A/AppData/Local/Programs/Python/Python314/python.exe"
Set-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)
& $python -m flask --app app run --host 127.0.0.1 --port 5000