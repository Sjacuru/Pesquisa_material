# Usage in PowerShell terminal (dot-source to persist in current session):
# . .\scripts\enable_search_debug.ps1

$env:PYTHONPATH = "."
$env:SEARCH_RELEVANCE_DEBUG = "1"
$env:KALUNGA_DEBUG = "1"
$env:KALUNGA_DEBUG_DUMP_DIR = "var/debug/kalunga"

Write-Host "Debug environment variables enabled for current terminal session:" -ForegroundColor Green
Write-Host "  PYTHONPATH=$env:PYTHONPATH"
Write-Host "  SEARCH_RELEVANCE_DEBUG=$env:SEARCH_RELEVANCE_DEBUG"
Write-Host "  KALUNGA_DEBUG=$env:KALUNGA_DEBUG"
Write-Host "  KALUNGA_DEBUG_DUMP_DIR=$env:KALUNGA_DEBUG_DUMP_DIR"
