# Artist Relation Resolver Frontend
A gui application for the artist relation resolver api

## Formatting
Run format and lint checks with Ruff:
```bash
$ uv run ruff check .
```

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
Enable devenv (nixos only):
```bash 
$ devenv shell
```

Run script:
```bash 
$ uv run main.py --host endpoint.com --port 80
```

Alternatively, the `ARTIST_RESOLVER_HOST` and `ARTIST_RESOLVER_PORT` environment variables can be set.
Linux:
```bash 
$ export ARTIST_RESOLVER_HOST="endpoint.com"
$ export ARTIST_RESOLVER_PORT="80"
$ uv run main.py
```

Windows:
```powershell 
$ENV:ARTIST_RESOLVER_HOST = "endpoint.com"
$ENV:ARTIST_RESOLVER_PORT = "80"
uv run main.py
```


