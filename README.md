# Paytm A‑BRTS QR Code Generator

A simple, MIT‑licensed Vue 3 application to generate payment QR codes for Paytm Ahmedabad BRTS bus stations. Choose a station from a curated list, set size and error‑correction, preview, and download the PNG.

## Live Cloudflare Page

🔥 Visit the deployed app:
- https://abrts.prateekspace.eu.org/

> Community project — not affiliated with Paytm, AMC, or BRTS.

🌟 Inspired project:
- https://utsstationqrcode.com/

## Safety Warning

- Scan this code only when physically present at the selected QR Code from the dropdown station.

## Features

- Vue 3 + Vite, fast HMR and tiny production build.
- JSON‑driven configuration:
  - Station list (Paytm A‑BRTS stops)
  - QR sizes and error‑correction levels
  - Optional presets
- Custom dropdowns with animated chevrons; keyboard friendly.
- Light/Dark/System theme via CSS variables.
- PNG download of the generated QR.
- Config validation with a clear error banner when public/input.json is invalid.
- Dockerized production image (Nginx) and compose file.

## Demo

Build locally or deploy using the instructions below. After building, serve dist/ from any static host or run the provided Docker image.

## Getting Started

### Prerequisites
- Node.js 18+ (or Docker)
- npm

### Install & Run (Development)
```bash
npm install
npm run dev
# open http://localhost:5173
```

### Build (Production)
```bash
npm run build
# output in dist/
```

### Lint/Format config (input.json)
```bash
npm run format:input
# pretty-prints public/input.json
```

## Configuration

The application loads settings from public/input.json.

Example:
```json
{
  "sizes": [
    { "label": "Small (128x128)", "value": 128 },
    { "label": "Medium (256x256)", "value": 256 },
    { "label": "Large (512x512)", "value": 512 }
  ],
  "errorCorrections": [
    { "label": "Low (L)", "value": "L" },
    { "label": "Medium (M)", "value": "M" },
    { "label": "Quartile (Q)", "value": "Q" },
    { "label": "High (H)", "value": "H" }
  ],
  "presets": [
    {
      "name": "A-BRTS Station A",
      "text": "Blank Data",
      "size": 512,
      "ecl": "H"
    },
    {
      "name": "A-BRTS Station B",
      "text": "Blank Data",
      "size": 512,
      "ecl": "H"
    },
    {
      "name": "A-BRTS Station C",
      "text": "Blank Data",
      "size": 512,
      "ecl": "H"
    }
  ]
}
```

Notes:
- If parsing or schema validation fails, an error banner appears and safe defaults load so the UI remains usable.
- Update stations under "stations". Validate/format via npm run format:input.

## Theming

- “Menu” in the header toggles Light/Dark/System.
- All colors are driven by CSS variables on the root .app element.

## Docker (Production)

Build and run:
```bash
docker compose up --build -d
# open http://localhost:8080
```

What’s included
- Multi‑stage Dockerfile (Node builder → Nginx runtime)
- docker-compose.yml (maps 8080→80)
- nginx.conf with SPA routing fallback and gzip

## Deployment

Static hosting (recommended for SPAs)
- Cloudflare Pages / Netlify / Vercel / GitHub Pages
  - Build command: npm run build
  - Output directory: dist
  - Enable SPA fallback to index.html (provider setting or redirects file)

Container hosting
- Fly.io / Railway / Render (use the provided Dockerfile)

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit with clear messages.
4. Open a Pull Request.

Guidelines
- Keep UI accessible (keyboard navigation, focus styles).
- Validate public/input.json with npm run format:input.
- Follow existing code style and theming tokens.

Want to add a new station?
- Open a Pull Request that includes either:
  - The Paytm QR code string (text) for the station; or
  - A clear picture of the station’s official Paytm QR (so the payload can be extracted/verified).
- Add the station name under "stations" in public/input.json and include your evidence in the PR.
- Contributions will be credited in the contributors section.

## Roadmap

- ✅ Enable search and filter functionality for stations within the dropdown menu.
- ⁉️ Consider adding QR scanner support for Rajkot, Surat, and Mumbai stations in the future, if required for approaching station.

## Disclaimer

This project is for educational and convenience purposes only and is not endorsed by Paytm or Ahmedabad BRTS. Always confirm payee details in the official Paytm interface before paying.

## License

MIT License

Copyright (c) 2025 Prateek Maru

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
