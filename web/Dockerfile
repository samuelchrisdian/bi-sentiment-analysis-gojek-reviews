# ---------- tahap build ----------
FROM node:24-alpine AS build
WORKDIR /app

# VITE_* di-inline saat BUILD, bukan dibaca saat container jalan. Karena itu
# alamat API masuk sebagai build arg — menaruhnya di `environment:` compose
# tidak akan berpengaruh apa pun pada bundel yang sudah jadi.
ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=$VITE_API_BASE

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- tahap sajian ----------
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost/ >/dev/null || exit 1
