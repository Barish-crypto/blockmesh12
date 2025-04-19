import requests
import time
import os
import threading
import random
import websocket
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║          BlockMesh Network AutoBot           ║
║     Github: https://github.com/IM-Hanzou     ║
║      Welcome and do with your own risk!      ║
╚══════════════════════════════════════════════╝
"""
    print(banner)

# Dictionaries to store tokens and authentication times
proxy_tokens = {}
proxy_auth_times = {}

def connect_websocket(email, api_token):
    try:
        import websocket._core as websocket_core
        ws = websocket_core.create_connection(
            f"wss://ws.blockmesh.xyz/ws?email={email}&api_token={api_token}",
            timeout=10
        )
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.GREEN} Connected to WebSocket")
        ws.close()
    except Exception as e:
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.YELLOW} WebSocket connection OK")

print_banner()
print(f"{Fore.YELLOW}Please Login to your Blockmesh Account first.{Style.RESET_ALL}\n")
email_input = input(f"{Fore.LIGHTBLUE_EX}Enter Email: {Style.RESET_ALL}")
password_input = input(f"{Fore.LIGHTBLUE_EX}Enter Password: {Style.RESET_ALL}")

login_endpoint = "https://api.blockmesh.xyz/api/get_token"
report_endpoint = "https://app.blockmesh.xyz/api/report_uptime?email={email}&api_token={api_token}"

login_headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://app.blockmesh.xyz",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

report_headers = {
    "accept": "*/*",
    "content-type": "text/plain;charset=UTF-8",
    "origin": "https://app.blockmesh.xyz",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

proxy_list_path = "proxies.txt"
proxies_list = []

if os.path.exists(proxy_list_path):
    with open(proxy_list_path, "r") as file:
        proxies_list = file.read().splitlines()
        print(f"{Fore.GREEN}[✓] Loaded {len(proxies_list)} proxies from proxies.txt")
else:
    print(f"{Fore.RED}[×] proxies.txt not found!")
    exit()

def format_proxy(proxy_string):
    """Format the proxy string into the correct dictionary format."""
    try:
        proxy_type, address = proxy_string.split("://")
        
        if "@" in address:
            credentials, host_port = address.split("@")
            username, password = credentials.split(":")
            host, port = host_port.split(":")
            proxy_dict = {
                "http": f"{proxy_type}://{username}:{password}@{host}:{port}",
                "https": f"{proxy_type}://{username}:{password}@{host}:{port}"
            }
        else:
            host, port = address.split(":")
            proxy_dict = {
                "http": f"{proxy_type}://{host}:{port}",
                "https": f"{proxy_type}://{host}:{port}"
            }
        
        return proxy_dict, host
    except ValueError as e:
        print(f"{Fore.RED}Invalid proxy format: {proxy_string}")
        return None, None

def authenticate(proxy):
    """Authenticate using the given proxy and return the API token."""
    proxy_config, ip_address = format_proxy(proxy)
    if not proxy_config:
        return None, None
    
    if proxy in proxy_tokens:
        return proxy_tokens[proxy], ip_address
        
    login_data = {"email": email_input, "password": password_input}
    
    try:
        response = requests.post(login_endpoint, json=login_data, headers=login_headers, proxies=proxy_config)
        response.raise_for_status()
        auth_data = response.json()
        api_token = auth_data.get("api_token")
        
        proxy_tokens[proxy] = api_token
        proxy_auth_times[proxy] = time.time()  # Record the authentication time
        
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.GREEN} Login successful {Fore.MAGENTA}|{Fore.LIGHTYELLOW_EX} {ip_address} {Style.RESET_ALL}")
        return api_token, ip_address
    except requests.RequestException as err:
        return None, None

def send_uptime_report(api_token, proxy):
    """Send uptime report to the Blockmesh server."""
    proxy_config, _ = format_proxy(proxy)
    if not proxy_config:
        return
    
    formatted_url = report_endpoint.format(email=email_input, api_token=api_token)
    
    try:
        response = requests.post(formatted_url, headers=report_headers, proxies=proxy_config)
        response.raise_for_status()
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.LIGHTGREEN_EX} PING successful {Fore.MAGENTA}| {Fore.MAGENTA}| {Fore.LIGHTWHITE_EX}{api_token}")
    except requests.RequestException as err:
        if proxy in proxy_tokens:
            del proxy_tokens[proxy]
        if proxy in proxy_auth_times:
            del proxy_auth_times[proxy]
        print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.RED} Failed to PING {Fore.MAGENTA}| {err}{Style.RESET_ALL}")

def process_proxy(proxy):
    """Process each proxy in a separate thread."""
    first_run = True
    while True:
        current_time = time.time()
        
        # Re-authenticate if first run, token missing, or 1 hour has passed
        if first_run or proxy not in proxy_tokens or (proxy in proxy_auth_times and current_time - proxy_auth_times[proxy] >= 3600):
            api_token, ip_address = authenticate(proxy)
            first_run = False
        else:
            api_token = proxy_tokens[proxy]
            proxy_config, ip_address = format_proxy(proxy)
        
        if api_token and ip_address:
            connect_websocket(email_input, api_token)
            # send_uptime_report(api_token, proxy)
        
        time.sleep(random.randint(60, 120))  # Random delay between cycles

def main():
    print(f"\n{Style.BRIGHT}Starting ...")
    threads = []
    for proxy in proxies_list:
        thread = threading.Thread(target=process_proxy, args=(proxy,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(1)
    
    print(f"{Fore.LIGHTCYAN_EX}[{datetime.now().strftime('%H:%M:%S')}]{Fore.LIGHTCYAN_EX}[✓] DONE! Delay before next cycle. Not Stuck! Just wait and relax...{Style.RESET_ALL}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping ...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {str(e)}")
