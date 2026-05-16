# AutoDocThinker Frontend

Modern React frontend for the AutoDocThinker AI Document Intelligence platform.

## Tech Stack

- **React 19** — UI framework
- **Vite 7** — Build tool & dev server
- **Vanilla CSS** — Custom design system with soft glow aesthetics

## Getting Started

```bash
npm install
npm run dev
```

Dev server runs at `http://localhost:5173` and proxies API requests to the backend at `http://localhost:5000`.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Chat | `/` | AI-powered document Q&A with session management |
| Domains | Sidebar | Browse registered knowledge domains |
| Ingestion | Sidebar | Import documents into the index |
| Index | Sidebar | View and manage the search index |
| Admin | Sidebar | System overview and RAG configuration |

## Build

```bash
npm run build
```

Production output is in `dist/`.
