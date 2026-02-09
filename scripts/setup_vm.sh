#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🚀 RobovAI Nova — Google Cloud VM Setup Script
# Run on a fresh Ubuntu 22.04+ VM
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════"
echo "  RobovAI Nova — VM Setup"
echo "═══════════════════════════════════════════════"

# 1. System Updates
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3.11 python3.11-venv python3-pip git nginx certbot python3-certbot-nginx ufw

# 2. Firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# 3. Clone repo (update URL)
cd /opt
sudo git clone https://github.com/m0shaban/RobovAI-Nova.git robovai
sudo chown -R $USER:$USER /opt/robovai
cd /opt/robovai

# 4. Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Create .env file (EDIT THIS!)
cat > .env << 'ENVEOF'
# ═══ EDIT THESE VALUES ═══
GROQ_API_KEY=your_key_here
GROQ_API_KEY_2=your_key_here
GROQ_API_KEY_3=your_key_here
GROQ_API_KEY_4=your_key_here
NVIDIA_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here

# Payment (add whichever you use)
# STRIPE_SECRET_KEY=sk_live_...
# STRIPE_WEBHOOK_SECRET=whsec_...
# PAYMOB_API_KEY=your_paymob_key
# PAYMOB_INTEGRATION_ID=your_integration_id
# PAYMOB_IFRAME_ID=your_iframe_id
# PAYMOB_HMAC_SECRET=your_hmac

EXTERNAL_URL=https://yourdomain.com
ENVEOF

echo "⚠️  Edit /opt/robovai/.env with your actual API keys!"

# 6. Systemd service
sudo cat > /etc/systemd/system/robovai.service << 'EOF'
[Unit]
Description=RobovAI Nova API
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=/opt/robovai
Environment=PATH=/opt/robovai/.venv/bin
ExecStart=/opt/robovai/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable robovai
sudo systemctl start robovai

# 7. Nginx reverse proxy
sudo cat > /etc/nginx/sites-available/robovai << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/robovai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ RobovAI Nova is running!"
echo "  🌐 http://$(curl -s ifconfig.me)"
echo ""
echo "  Next steps:"
echo "  1. Edit /opt/robovai/.env with real API keys"
echo "  2. sudo systemctl restart robovai"
echo "  3. For HTTPS with domain:"
echo "     sudo certbot --nginx -d yourdomain.com"
echo "═══════════════════════════════════════════════"
