#!/data/data/com.termux/files/usr/bin/bash
echo "[+] Installing Real Number Tracker..."

# Update and install dependencies
pkg update -y && pkg upgrade -y
pkg install -y python git curl wget

# Install Python packages
pip install --upgrade pip
pip install phonenumbers requests beautifulsoup4 colorama

# Install PhoneInfoga
echo "[+] Installing PhoneInfoga..."
git clone https://github.com/sundowndev/phoneinfoga.git
cd phoneinfoga
pip install -r requirements.txt
chmod +x phoneinfoga.py

# Download tracker script
cd $HOME
curl -O https://raw.githubusercontent.com/Deat-Evil-bit/real-tracker/main/real_tracker.py
chmod +x real_tracker.py

echo "[+] Installation complete!"
echo "[+] Run: python real_tracker.py"
