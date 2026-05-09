# Artist Relation Resolver Frontend
A gui application for the artist relation resolver api

## Updating dependencies
- Manually update the python version in `devenv.nix`
- Manually update the python version in `pyproject.toml`
- Update devenv:
```bash
devenv update
```

- Update outdated libraries:
```bash
$ uv tree --outdated --depth 1
$ uv add 'httpx~=0.28.0'
#or 
$ uv add --dev 'httpx~=0.28.0'
```
uv automatically upgrades versions matching the constraint, and will do so silently, they will not be listed in the outdated packages. `uv tree --outdated` only highlights packages that need to be upgraded manually.

## Running
### Linux
Enable devenv:
```bash 
$ devenv shell
```
run script:
```bash 
$ uv run main.py --host endpoint.com --port 80
```

Alternatively, the `ARTIST_RESOLVER_HOST` and `ARTIST_RESOLVER_PORT` environment variables can be set:
```bash 
$ export ARTIST_RESOLVER_HOST="endpoint.com"
$ export ARTIST_RESOLVER_PORT="80"
$ uv run main.py
```

### Windows
The host and port for the api server needs to be provided to the application by using the --host and --port parameters:
```powershell 
uv run main.py --host endpoint.com --port 80
```
Alternatively, the `ARTIST_RESOLVER_HOST` and `ARTIST_RESOLVER_PORT` environment variables can be set:

```powershell 
$ENV:ARTIST_RESOLVER_HOST = "endpoint.com"
$ENV:ARTIST_RESOLVER_PORT = "80"
uv run main.py
```

The project root contains a run.ps1 which runs the python script. Dependencies still need to be installed manually. Note that this expects the correct environment variables to be set:

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

