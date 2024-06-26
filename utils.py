import data
import sys, os, time, requests, json, base64, tempfile
from downloader import download
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from packaging import version


DATA_FOLDER = f"{tempfile.gettempdir()}\\ImagineSuiteData"
GENERATIONS_FOLDER = f"{DATA_FOLDER}\\Generations"
VERSION = "v1.1.0"
RELEASE_LINK = "https://github.com/TheNebulo/ImagineSuite/releases/latest"
FILE_NAME = "ImagineSuite.exe"
DEFAULT_CONFIG = {
    "BATCH_SIZE" : {
        "value" : 3,
        "min_value" : 1,
        "max_value" : 10,
        "description" : "Amount of images to render in one batch."
    },
    "MAX_IMAGES" : {
        "value" : 30,
        "min_value" : 1,
        "max_value" : 100,
        "description" : "Maximum amount of images to render in one request (total between batches)."
    },
    "BATCH_TIMEOUT" : {
        "value" : 45,
        "min_value" : 5,
        "max_value" : 120,
        "description" : "Timeout (in seconds) between batches to avoid rate limits."   
    },
    "ALWAYS_VERIFY_KEYS" : {
        "value" : False,
        "description" : "Whether to force verify all entered API keys."
    }
}

EMOJIS = {
    "success" : ":white_heavy_check_mark:",
    "warning" : ":construction:",
    "debug" : ":wrench:",
    "error" : ":x:",
    "update" : ":package:"
}

SERVICES = data.SERVICES

last_known_online = True

def valid_generation_image(file_name):
    if file_name.endswith(".png") or file_name.endswith(".jpeg") or file_name.endswith(".jpg"): return True
    return False

def base64_json_to_image(base64_json_str, output_file_path):
    image_data = base64.b64decode(base64_json_str)

    with open(output_file_path, 'wb') as file:
        file.write(image_data)
        
def url_to_image(image_url, output_file_path):
    image_data = requests.get(image_url).content
    
    with open(output_file_path, 'wb') as file:
        file.write(image_data)

def flush_input_buffer():
    try:
        import msvcrt # x86
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios # Linux/Unix
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)

def prompt_input(msg, choices=None):
    flush_input_buffer()
    response = Prompt.ask(msg, choices=choices)
    return response

def confirm_input(msg):
    flush_input_buffer()
    response = Confirm.ask(msg)
    return response

def is_online():
    global last_known_online
    try: requests.get(RELEASE_LINK)
    except:
        last_known_online = False 
        return False
    else:
        last_known_online = True 
        return True  
    
def debug(msg, level=None, console = Console(), highlight=True):
    if not level: console.log(msg, highlight=highlight, _stack_offset=2)
    else: console.log(f"{EMOJIS[level]} {msg}", highlight=highlight, _stack_offset=2)

def print(msg, level=None, console = Console(), highlight=True):
    if not level: console.print(msg, highlight=highlight)
    else: console.print(f"{EMOJIS[level]} {msg}", highlight=highlight)
    
def print_header(console = None, check_online = False, show_reconnect_info = False):
    name = Text("ImagineSuite", justify="center", style="bold cyan")
    if check_online:
        if not last_known_online and show_reconnect_info > 0:
            with console.status("[bold green] Trying to re-establish internet connection...", spinner="arc"): 
                time.sleep(1)
                is_online()
            if last_known_online: debug("Re-established internet connection!", level='success', console=console)
            else: debug("Failed to re-establish internet connection.", level='error', console=console)
            time.sleep(1)
            console.clear()
        elif show_reconnect_info == 1:
            with console.status("[bold green] Confirming internet connection...", spinner="arc"):
                time.sleep(1) 
                is_online()
            if last_known_online: debug("Internet connection confirmed!", level='success', console=console)
            else: debug("Failed to establish internet connection.", level='error', console=console)
            time.sleep(1)
            console.clear()
        else: is_online()
    if not last_known_online: name = Text("[OFFLINE] ", justify="center", style="bold red") + name
    header = Panel(name, title=f"[bold]{VERSION}", subtitle="[italic]By TheNebulo")
    if console: print(header, console=console)
    else: print(header)

def clear_console(timeout = 0, header = True, console = Console(), check_online = False, show_reconnect_info = 0):
    # Reconnect info: 0 = Don't show, 1 = Always show, 2 = Only if was offline
    time.sleep(timeout)
    console.clear()
    
    # This is just in case the console doesn't clear properly (cough cough Windows 10 cough cough)
    if os.name == 'nt': os.system('cls')
    else: os.system('clear')
    
    if header: print_header(console, check_online, show_reconnect_info)

def get_application_path():
    return sys.argv[0]

def get_working_dir_path():
    return os.getcwd().replace("\\","/")

def initial_launch_exe():
    return sys.argv[0].split(".")[-1] == "exe"

def is_exe():
    if initial_launch_exe(): return True
    return initial_launch_exe() or os.environ.get('RUNNING_AS_EXE', '0') == '1'
    
def is_latest():
    response = requests.get(RELEASE_LINK)
    latest_version = response.url.split("/").pop()

    current_ver = version.parse(VERSION.lstrip('v'))
    latest_ver = version.parse(latest_version.lstrip('v'))

    return current_ver >= latest_ver
    
def restart():
    clear_console(header=False)
    if is_exe():
        os.environ['RUNNING_AS_EXE'] = '1'  
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        print("Restarting the app isn't available when running the Python script!", level="error")
        prompt_input("Press enter to quit the app")
        clear_console(header=False)
        sys.exit()

def update_app():
    try: latest = is_latest()
    except:
        debug("Failed to establish connection with ImagineSuite!", level='error')
        time.sleep(1)
        return   
    if latest == True:
        debug("ImagineSuite is already up-to-date!", level='success')
        time.sleep(3)
        return
    else:
        download_link = f"{RELEASE_LINK}/download/{FILE_NAME}"
        try:
            download(download_link, DATA_FOLDER)
        except:
            debug("Failed to download new version of ImagineSuite!", level='error')
            debug("[bold]Check your internet connection and try again![/bold]")
            time.sleep(3)
            return   
        dest_path = get_application_path()
        src_path = f"{get_working_dir_path()}/{DATA_FOLDER}/{FILE_NAME}"
        temp_path = f"{get_working_dir_path()}/{DATA_FOLDER}/temp.exe"
        os.rename(dest_path, temp_path)
        os.rename(src_path, dest_path)
        debug("Installed new version of ImagineSuite! Restarting.", level='success')
        time.sleep(2)
        restart()
    
def get_user_name():
    if os.name == 'nt':
        import ctypes
        GetUserNameExW = ctypes.windll.secur32.GetUserNameExW
        name_display = 3

        size = ctypes.pointer(ctypes.c_ulong(0))
        GetUserNameExW(name_display, None, size)

        name_buffer = ctypes.create_unicode_buffer(size.contents.value)
        GetUserNameExW(name_display, name_buffer, size)
        return name_buffer.value if name_buffer.value != "" else "User"
    else:
        import pwd
        display_name = (entry[4] for entry in pwd.getpwall() if entry[2] == os.geteuid()).next()
        return display_name if display_name != "" else "User"

def clean_env_file():
    env_path = DATA_FOLDER+"/.env"
    
    with open(env_path, 'r') as file:
        lines = file.readlines()
        
    env_dict = {}
    for line in lines:
        line = line.strip()
        if not line: continue

        comment_pos = line.find('#')
        if comment_pos != -1:
            if comment_pos == 0: continue
            else: line = line[:comment_pos].strip() 

        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('\'"') 
            if key and value and key in SERVICES.keys():
                env_dict[key] = value

    with open(env_path, 'w') as file:
        for key, value in env_dict.items():
            if value:
                file.write(f'{key}={value}\n')


    
def edit_or_add_env_value(key_to_edit, new_value):
    env_path = DATA_FOLDER + "/.env"
    clean_env_file()

    with open(env_path, 'r') as file:
        lines = file.readlines()

    env_dict = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_dict[k.strip()] = v.strip().strip('\'"')
    
    if new_value is None:
        if key_to_edit in env_dict:
            del env_dict[key_to_edit]
    else:
        env_dict[key_to_edit] = new_value

    with open(env_path, 'w') as file:
        for key, value in env_dict.items():
            file.write(f'{key}={value}\n')
            
def clean_config_file(console, verbose = False):
    config_path = f"{DATA_FOLDER}/config.json"
        
    changed = False
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f: loaded_config = json.load(f)
        except:
            if verbose:
                debug("Config file corrupted! Restoring to default.", level="error", console=console)
                time.sleep(1)
            changed = True
            with open(config_path, 'w') as f: json.dump(DEFAULT_CONFIG, f)
            loaded_config = DEFAULT_CONFIG
    else:
        if verbose:
            debug("Missing config file. Creating new config file.", level="warning", console=console)
            time.sleep(1)
        changed = True
        with open(config_path, 'w') as f: json.dump(DEFAULT_CONFIG, f)
        loaded_config = DEFAULT_CONFIG 
            
    if type(loaded_config) == dict:
        for key in DEFAULT_CONFIG.keys():
            try:
                loaded_config[key]
            except:
                if verbose:
                    debug(f"Config rule '{key}' missing! Restoring to default.", level="error", console=console)
                    time.sleep(1)
                changed = True
                loaded_config[key] = DEFAULT_CONFIG[key]
            else:
                if not isinstance(loaded_config, dict):
                    if verbose:
                        debug(f"Config rule '{key}' corrupted! Restoring to default.", level="error", console=console)
                        time.sleep(1)
                    changed = True
                    loaded_config[key] = DEFAULT_CONFIG[key]
                else:
                    try:
                        if type(loaded_config[key]['value']) != type(DEFAULT_CONFIG[key]['value']):
                            if verbose: 
                                debug(f"Config rule '{key}'s value is corrupted! Restoring to default.", level="error", console=console)
                                time.sleep(1)
                            changed = True
                            loaded_config[key]['value'] = DEFAULT_CONFIG[key]['value']
                        if loaded_config[key]['description'] != DEFAULT_CONFIG[key]['description']:
                            if verbose: 
                                debug(f"Config rule '{key}'s description is corrupted! Restoring to default.", level="error", console=console) 
                                time.sleep(1)
                            changed = True
                            loaded_config[key]['description'] = DEFAULT_CONFIG[key]['description']
                        if DEFAULT_CONFIG[key].get('min_value'):
                            if loaded_config[key]['min_value'] != DEFAULT_CONFIG[key]['min_value']:
                                if verbose: 
                                    debug(f"Config rule '{key}'s minimum value is corrupted! Restoring to default.", level="error", console=console) 
                                    time.sleep(1)
                                changed = True
                                loaded_config[key]['min_value'] = DEFAULT_CONFIG[key]['min_value']
                            if loaded_config[key]['value'] < DEFAULT_CONFIG[key]['min_value']:
                                if verbose: 
                                    debug(f"Config rule '{key}'s value is below minimum! Restoring to default.", level="error", console=console)
                                    time.sleep(1) 
                                changed = True
                                loaded_config[key]['value'] = DEFAULT_CONFIG[key]['value']
                        if DEFAULT_CONFIG[key].get('max_value'):
                            if loaded_config[key]['max_value'] != DEFAULT_CONFIG[key]['max_value']:
                                if verbose: 
                                    debug(f"Config rule '{key}'s maximum value is corrupted! Restoring to default.", level="error", console=console)
                                    time.sleep(1)
                                changed = True
                                loaded_config[key]['max_value'] = DEFAULT_CONFIG[key]['max_value']
                            if loaded_config[key]['value'] > DEFAULT_CONFIG[key]['max_value']:
                                if verbose: 
                                    debug(f"Config rule '{key}'s value is above maximum! Restoring to default.", level="error", console=console)
                                    time.sleep(1) 
                                changed = True
                                loaded_config[key]['value'] = DEFAULT_CONFIG[key]['value']
                    except:
                        if verbose: 
                            debug(f"Config rule '{key}' corrupted! Restoring to default.", level="error", console=console)
                            time.sleep(1)
                        changed = True
                        loaded_config[key] = DEFAULT_CONFIG[key]           
    else:
        if verbose: 
            debug("Config file corrupted! Restoring to default.", level="error", console=console)
            time.sleep(1)
        changed = True
        with open(config_path, 'w') as f: json.dump(DEFAULT_CONFIG, f)
        loaded_config = DEFAULT_CONFIG
    
    modified_config = {}
    for key in loaded_config.keys():
        if key in DEFAULT_CONFIG.keys(): modified_config[key] = loaded_config[key]
    loaded_config = modified_config
    with open(config_path, 'w') as f: json.dump(loaded_config, f)
    time.sleep(1)
    return loaded_config, changed