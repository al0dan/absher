#!/bin/bash
# One-command VPS setup
echo "Setting up Uqood Absher Environment..."

# System Updates
apt update && apt upgrade -y

# Dependencies
apt install python3-pip python3-venv ufw -y

# Firewall
ufw allow 5000/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Application Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create Service
cat > start.sh <<EOF
#!/bin/bash
source venv/bin/activate
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
EOF
chmod +x start.sh

# PM2 Setup (requires Node.js, assuming installed or use systemd if preferred, user asked for PM2)
# Installing Node.js for PM2
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt install -y nodejs
npm install -g pm2

pm2 start start.sh --name uqood-app
pm2 save
pm2 startup

echo "Deployment Complete! App running on port 5000."
