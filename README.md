# Artist Relation Resolver Frontend
A gui application for the artist relation resolver api

## Installing dependencies
Create a virtual environment
```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r ./requirements.txt
```

Check for outdated libraries:
```powershell
pip list --outdated
python.exe -m pip install --upgrade [packagename]
pip freeze > requirements.txt
```
When freezing requirements, make sture manually check the created file to only include top-level packages, and set all packages to match by '~=' instead of '==' to always install the lastest patch version of a package.

## Running
The host and port for the api server needs to be provided to the application by using the --host and --port parameters:
```powershell 
./.venv/Scripts/Activate.ps1
python -m main --host endpoint.com --port 80
```
Alternatively, the `ARTIST_RESOLVER_HOST` and `ARTIST_RESOLVER_PORT` environment variables can be set:

```powershell 
./.venv/Scripts/Activate.ps1
$ENV:ARTIST_RESOLVER_HOST = "endpoint.com"
$ENV:ARTIST_RESOLVER_PORT = "80"
python -m main
```

The project root contains a run.ps1 which verifies that all dependencies are installed and then runs the python script. Note that this expects the correct environment variables to be set:

```powershell 
$ENV:ARTIST_RESOLVER_HOST = "endpoint.com"
$ENV:ARTIST_RESOLVER_PORT = "80"
./main.py
```

To create a one-click shortcut, use the following properties:
Start in:
`<Project Directory>`
Target:
`pwsh -noprofile -WindowStyle Hidden -command "&{$ENV:ARTIST_RESOLVER_HOST='endpoint.com';$ENV:ARTIST_RESOLVER_PORT='80';& '<Project Directory>/run.ps1'}"`

## Cleanup
To clean up environment when done
```powershell
deactivate
Remove-Item -Path ./.venv/ -Recurse -Force
```