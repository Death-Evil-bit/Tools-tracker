#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import json
import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from bs4 import BeautifulSoup
import subprocess
from datetime import datetime

class RealNumberTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
        })
    
    def get_truecaller_info(self, number):
        """Get info from Truecaller"""
        try:
            url = f"https://truecaller.com/search/in/{number}"
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Extract name
                name_tag = soup.find('h1', class_='profile-name')
                name = name_tag.text.strip() if name_tag else "Not Found"
                
                # Extract location
                location_tag = soup.find('div', class_='location')
                location = location_tag.text.strip() if location_tag else "Unknown"
                
                # Extract carrier
                carrier_tag = soup.find('div', class_='carrier')
                carrier_info = carrier_tag.text.strip() if carrier_tag else "Unknown"
                
                return {
                    'name': name,
                    'location': location,
                    'carrier': carrier_info,
                    'source': 'Truecaller'
                }
        except:
            pass
        return None
    
    def get_openphonebook(self, number):
        """Get from OpenPhonebook"""
        try:
            url = f"https://www.openphonebook.com/{number}"
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                
                results = {}
                # Parse table data
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            key = cols[0].text.strip().replace(':', '')
                            value = cols[1].text.strip()
                            results[key] = value
                
                if results:
                    return {
                        'data': results,
                        'source': 'OpenPhonebook'
                    }
        except:
            pass
        return None
    
    def check_social_media(self, number):
        """Check social media presence"""
        social_results = {}
        
        # Format for search
        clean_num = number.replace('+', '').replace(' ', '')
        
        # WhatsApp check
        try:
            whatsapp_url = f"https://wa.me/{clean_num}"
            r = self.session.head(whatsapp_url, timeout=5)
            if r.status_code in [200, 302]:
                social_results['WhatsApp'] = whatsapp_url
        except:
            pass
        
        # Telegram check
        try:
            telegram_url = f"https://t.me/{clean_num}"
            r = self.session.head(telegram_url, timeout=5)
            if r.status_code == 200:
                social_results['Telegram'] = telegram_url
        except:
            pass
        
        # Facebook search URL
        facebook_url = f"https://www.facebook.com/search/top/?q={clean_num}"
        social_results['Facebook_Search'] = facebook_url
        
        return social_results
    
    def get_phoneinfoga_scan(self, number):
        """Use PhoneInfoga API"""
        try:
            # Local phoneinfoga if installed
            cmd = f"phoneinfoga scan -n {number} --no-ansi"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                # Parse output
                lines = output.split('\n')
                info = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                return info
        except:
            pass
        
        # Try online API
        try:
            url = f"https://api.phoneinfoga.crvx.fr/api/numbers/{number}/scan/local"
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        
        return None
    
    def validate_number(self, number):
        """Validate phone number using phonenumbers library"""
        try:
            parsed = phonenumbers.parse(number, None)
            if phonenumbers.is_valid_number(parsed):
                return {
                    'valid': True,
                    'international': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                    'national': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
                    'country': geocoder.description_for_number(parsed, "en"),
                    'carrier': carrier.name_for_number(parsed, "en"),
                    'timezone': timezone.time_zones_for_number(parsed)
                }
        except:
            pass
        return {'valid': False}
    
    def scan_number(self, number):
        """Main scanning function"""
        print(f"\n[+] Scanning: {number}")
        print("[+] This may take a moment...\n")
        
        all_results = {}
        
        # Step 1: Basic validation
        print("[1/5] Validating number...")
        validation = self.validate_number(number)
        all_results['validation'] = validation
        
        if not validation['valid']:
            print("[-] Invalid phone number format!")
            return all_results
        
        # Step 2: Truecaller lookup
        print("[2/5] Checking Truecaller...")
        truecaller = self.get_truecaller_info(number)
        if truecaller:
            all_results['truecaller'] = truecaller
        
        # Step 3: OpenPhonebook
        print("[3/5] Checking public directories...")
        openphonebook = self.get_openphonebook(number)
        if openphonebook:
            all_results['openphonebook'] = openphonebook
        
        # Step 4: Social media
        print("[4/5] Checking social media...")
        social = self.check_social_media(number)
        if social:
            all_results['social_media'] = social
        
        # Step 5: PhoneInfoga
        print("[5/5] Running advanced scan...")
        phoneinfoga = self.get_phoneinfoga_scan(number)
        if phoneinfoga:
            all_results['phoneinfoga'] = phoneinfoga
        
        return all_results
    
    def display_results(self, results, number):
        """Display results in readable format"""
        print("\n" + "="*60)
        print(f"SCAN RESULTS FOR: {number}")
        print("="*60)
        
        if 'validation' in results:
            val = results['validation']
            if val['valid']:
                print("\n[✓] BASIC INFORMATION:")
                print(f"   • International: {val.get('international', 'N/A')}")
                print(f"   • National: {val.get('national', 'N/A')}")
                print(f"   • Country: {val.get('country', 'N/A')}")
                print(f"   • Carrier: {val.get('carrier', 'N/A')}")
                if val.get('timezone'):
                    print(f"   • Timezone: {', '.join(val['timezone'])}")
        
        if 'truecaller' in results:
            tc = results['truecaller']
            print("\n[✓] TRUECALLER DATA:")
            print(f"   • Name: {tc.get('name', 'N/A')}")
            print(f"   • Location: {tc.get('location', 'N/A')}")
            print(f"   • Carrier: {tc.get('carrier', 'N/A')}")
        
        if 'social_media' in results:
            social = results['social_media']
            print("\n[✓] SOCIAL MEDIA LINKS:")
            for platform, link in social.items():
                print(f"   • {platform}: {link}")
        
        if 'openphonebook' in results:
            opb = results['openphonebook']
            print("\n[✓] PUBLIC RECORDS:")
            for key, value in opb.get('data', {}).items():
                if value and value != 'N/A':
                    print(f"   • {key}: {value}")
        
        if 'phoneinfoga' in results:
            pi = results['phoneinfoga']
            if isinstance(pi, dict):
                print("\n[✓] TECHNICAL DATA:")
                for key, value in pi.items():
                    if value and str(value).strip():
                        print(f"   • {key}: {value}")
        
        print("\n" + "="*60)
    
    def save_report(self, results, number):
        """Save results to file"""
        filename = f"/sdcard/scan_{number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n[✓] Report saved to: {filename}")
        except:
            print(f"\n[!] Could not save to {filename}, trying current directory...")
            filename = f"scan_{number}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"[✓] Report saved to: {filename}")

def main():
    # Banner
    os.system('clear')
    print("""
    
    ██████╗ ███████╗ █████╗ ██╗      ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
    ██╔══██╗██╔════╝██╔══██╗██║      ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██████╔╝█████╗  ███████║██║         ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
    ██╔══██╗██╔══╝  ██╔══██║██║         ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ██║  ██║███████╗██║  ██║███████╗    ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    
    """)
    print(" " * 10 + "REAL NUMBER TRACKER - ACTUAL OSINT TOOL")
    print(" " * 15 + "Author: @Deat-Evil-bit")
    print("="*70)
    
    tracker = RealNumberTracker()
    
    while True:
        print("\nOptions:")
        print("1. Scan single number")
        print("2. Scan multiple numbers")
        print("3. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            number = input("\nEnter phone number (with country code, e.g., +628123456789): ").strip()
            if not number:
                print("[-] Please enter a valid number")
                continue
            
            results = tracker.scan_number(number)
            tracker.display_results(results, number)
            
            save = input("\nSave report? (y/n): ").strip().lower()
            if save == 'y':
                tracker.save_report(results, number)
            
            input("\nPress Enter to continue...")
            os.system('clear')
            
        elif choice == '2':
            numbers_input = input("\nEnter numbers separated by commas: ").strip()
            numbers = [n.strip() for n in numbers_input.split(',') if n.strip()]
            
            if not numbers:
                print("[-] No valid numbers provided")
                continue
            
            for num in numbers:
                print(f"\n{'='*40}")
                print(f"Scanning: {num}")
                print('='*40)
                results = tracker.scan_number(num)
                tracker.display_results(results, num)
                
                save = input("\nSave this report? (y/n): ").strip().lower()
                if save == 'y':
                    tracker.save_report(results, num)
            
            input("\nPress Enter to continue...")
            os.system('clear')
            
        elif choice == '3':
            print("\n[+] Exiting...")
            break
        
        else:
            print("[-] Invalid choice")

if __name__ == "__main__":
    main()
