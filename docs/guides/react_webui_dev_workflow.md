# React Web UI Dev Workflow (Connector + Simulator)

This repo ships two React SPAs built with **Vite + React + TypeScript**:

- **Connector UI**: `webui/apps/connector-ui` → served by `unified_connector` at `/`
  - Static prefix: `/static/connector-ui/`
  - Legacy fallback: `/legacy`
- **Simulator UI**: `webui/apps/simulator-ui` → served by `ot_simulator` at `/`
  - Static prefix: `/static/simulator-ui/`
  - Legacy fallback: `/legacy`

Both are designed to **not change** any existing REST/WebSocket contracts. Use the parity checklist:
`docs/guides/react_webui_parity_checklist.md`.

## Build the UIs (outputs into backend static dirs)

```bash
cd webui
npm ci
npm run build
```

Build outputs:
- `unified_connector/web/static/connector-ui/`
- `ot_simulator/web_ui/static/simulator-ui/`

## Run backends (React served by Python)

### Connector

```bash
python3.12 -m venv .venv312c
source .venv312c/bin/activate
pip install -r requirements.txt

python -m unified_connector
```

Open:
- React UI: `http://localhost:8080/`
- Legacy UI: `http://localhost:8080/legacy`

### Simulator

```bash
python3.12 -m venv .venv312c
source .venv312c/bin/activate
pip install -r requirements.txt

python -m ot_simulator --protocol all --web-ui
```

Open:
- React UI: `http://localhost:8989/`
- Legacy UI: `http://localhost:8989/legacy`

## E2E smoke tests (optional)

Playwright tests are present but are skipped unless you explicitly enable them:

```bash
cd webui
E2E=1 CONNECTOR_BASE_URL="http://localhost:8080" SIMULATOR_BASE_URL="http://localhost:8989" npm run test:e2e
```

## Aesthetic checklist (industrial SCADA control-room)

- **Grid + dark panels** present (global SCADA theme CSS in `@ot/ui-kit/scada.css`)
- **Diagnostics/log values render green** (KV values use `--text-accent` and `--status-running` tokens)
- **Dense operator layout** (sidebar + panels, minimal whitespace)
- **Legacy parity**: if behavior differs, compare with `/legacy` side-by-side before changing backend contracts

