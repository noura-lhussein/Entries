FROM node:22-bookworm

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 4201

# Compose overrides this to point the proxy at the backend service (web:8001).
# Bare `ng serve` picks up proxy.conf.json (→ localhost:8001) via angular.json.
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--port", "4201", "--proxy-config", "proxy.conf.docker.json"]
