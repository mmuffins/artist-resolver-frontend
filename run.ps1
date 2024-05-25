$venvName = ".venv"

if(-not (Test-Path -Path "./$venvName")){
  python -m venv $venvName
}

& "./$venvName/Scripts/Activate.ps1"

if(-not [bool]$env:VIRTUAL_ENV){
  Write-Error "Could not activate python virtual environment."
  Read-Host
  return
}

& pip install -r ./requirements/common.txt
python -m main