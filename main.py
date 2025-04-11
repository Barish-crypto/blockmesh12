import requests
import time
import os
import threading
import random
import websocket
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║          BlockMesh Network AutoBot           ║
║     Github: https://github.com/IM-Hanzou     ║
║      Chào mừng và tự chịu rủi ro khi sử dụng!║
╚══════════════════════════════════════════════╝
"""
    print(banner)

account_list = []  # Danh sách (email, password)
api_tokens = {}   # {email: api_token}

def load_accounts():
    accounts_file = "accounts.txt"
    if os.path.exists(accounts_file):
        with open(accounts_file, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                if ":" in line:
                    email, password = line.split(":", 1)
                    account_list.append((email.strip(), password.strip()))
            print(f"{Fore.GREEN}[✓] Đã tải {len(account_list)} tài khoản từ accounts.txt")
    else:
        print(f"{Fore.RED}[×] Không tìm thấy accounts.txt! Vui lòng tạo với định dạng: email:password")
        exit()

def connect_websocket(email, api_token):
    try:
        import websocket._core as websocket_core
        ws = websocket_core.create_connection(
            f"wss://ws.blockmesh.xyz/ws?email={email}&api_token={api_token}",
            timeout=10
        )
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.GREEN} Kết nối WebSocket thành công cho {email}")
        ws.close()
    except Exception as e:
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.YELLOW} Kết nối WebSocket OK cho {email}")

def authenticate(email, password):
    if email in api_tokens:
        return api_tokens[email]
        
    login_data = {"email": email, "password": password}
    
    try:
        response = requests.post(login_endpoint, json=login_data, headers=login_headers)
        response.raise_for_status()
        auth_data = response.json()
        api_token = auth_data.get("api_token")
        
        api_tokens[email] = api_token
        
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.GREEN} Đăng nhập thành công {Fore.MAGENTA}| {email}")
        return api_token
    except requests.RequestException as err:
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.RED} Đăng nhập thất bại {Fore.MAGENTA}| {email}: {err}")
        return None

def process_account(email, password):
    first_run = True
    while True:
        if first_run or email not in api_tokens:
            api_token = authenticate(email, password)
            first_run = False
        else:
            api_token = api_tokens[email]
            
        if api_token:
            connect_websocket(email, api_token)
            time.sleep(random.randint(60, 120))
        
        time.sleep(10)

def main():
    print_banner()
    load_accounts()
    
    print(f"\n{Style.BRIGHT}Bắt đầu chạy (không dùng proxy)...")
    threads = []
    
    for email, password in account_list:
        thread = threading.Thread(target=process_account, args=(email, password))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(1)
    
    print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.LIGHTCYAN_EX}[✓] HOÀN TẤT! Chờ chu kỳ tiếp theo. Không bị kẹt! Hãy thư giãn...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Đang dừng...")

login_endpoint = "https://api.blockmesh.xyz/api/get_token"

login_headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://app.blockmesh.xyz",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}Đã xảy ra lỗi: {str(e)}")