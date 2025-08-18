# ---------- 1) Builder: install deps, format JSON, build ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Install minimal tools (optional)
RUN apk add --no-cache git

# Leverage layer caching for deps
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./

# Prefer npm ci when lockfile present
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Bring in the rest of the project
COPY . .

# Ensure a format:input script exists; add it if missing (defensive)
RUN node -e "const fs=require('fs');const p=require('./package.json');p.scripts=p.scripts||{};if(!p.scripts['format:input']){p.scripts['format:input']='prettier --write public/input.json'};fs.writeFileSync('package.json',JSON.stringify(p,null,2));"

# Pretty-print the config JSON (no-op if Prettier missing, but we include it in devDeps)
RUN npx --yes prettier --version && npm run format:input || true

# Build production bundle
RUN npm run build

# ---------- 2) Runtime: Nginx serves the built files ----------
FROM nginx:1.27-alpine AS runtime

# Copy custom nginx.conf (placed at project root)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output to Nginx web root
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
