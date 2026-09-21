#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

NGINX_CONF="/etc/nginx/sites-available/verimate"
BACKUP_CONF="/etc/nginx/sites-available/verimate.bak.$(date +%s)"

if [ -f "$NGINX_CONF" ]; then
    echo "Backing up existing configuration to $BACKUP_CONF..."
    cp "$NGINX_CONF" "$BACKUP_CONF"
fi

echo "Writing updated Nginx configuration for port 8015..."
cat << 'EOF' > "$NGINX_CONF"
server {
    listen 8015;

    client_max_body_size 50M;

    # Oxygen RISC-V Simulator (Application & Static Assets via WhiteNoise)
    location /oxygen {
        proxy_pass http://127.0.0.1:8016;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Verimate Frontend (Vite React Dev Server)
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Verimate Backend API (Flask / Gunicorn)
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        send_timeout 600s;
    }
}
EOF

echo "Testing Nginx configuration..."
nginx -t

echo "Reloading Nginx..."
systemctl reload nginx

echo "Success! Nginx on port 8015 is now proxying /oxygen and static files properly."
