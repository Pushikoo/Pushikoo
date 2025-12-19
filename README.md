# Pushikoo

A message sync framework.

## Development

### Backend

```sh
cd backend
uv sync

python src/pushikoo/main.py
```

### Frontend

```sh
cd frontend

pnpm install
pnpm dev
```

### Sync API Changes and Generate Frontend Client

```sh
# Stay in root directory
./backend/.venv/scripts/activate
python script/generate_client.py
```

### Build

```sh
# Stay in root directory
./backend/.venv/scripts/activate
python script/build.py
```
