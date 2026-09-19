# =============================================================================
# Production Dockerfile for AML Investigator Dashboard (React + Vite)
# Multi-stage Node.js build to Nginx Alpine runner
# =============================================================================

# Build stage
FROM node:20-alpine as builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# Runner stage
FROM nginx:alpine as runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
