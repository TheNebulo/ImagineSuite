import utils
import os, time, json, sys, dotenv, datetime, shutil, webbrowser
from rich.console import Console
from rich.table import Table

console = Console()
loaded_config = new_data = None

def initialise_data():
    env_path = utils.DATA_FOLDER+"/.env"
    
    utils.clear_console()

    with console.status("[bold green] Launching ImagineSuite...", spinner="arc"):
        time.sleep(1)
        
        if os.path.exists(f"{utils.DATA_FOLDER}/temp.exe"):
            os.remove(f"{utils.DATA_FOLDER}/temp.exe")
            utils.debug(f"Successfully updated ImagineSuite to {utils.VERSION}!", level="update")
            time.sleep(1)
            
        if not utils.is_online():
            utils.debug("Failed to connect establish internet connection. Functionality will be severly limited.", level="warning", console=console)
            time.sleep(1)
        
        if not os.path.exists(utils.DATA_FOLDER):
            utils.debug("Data folder missing. Creating new data folder.", level="warning", console=console)
            os.mkdir(utils.DATA_FOLDER)
            new_data = True
            time.sleep(1)
        else: new_data = False

        if not os.path.exists(utils.GENERATIONS_FOLDER):
            utils.debug("Generations folder missing. Creating new generations folder.", level="warning", console=console)
            os.mkdir(utils.GENERATIONS_FOLDER)
            time.sleep(1)
        
        loaded_config, changed = utils.clean_config_file(console, verbose=True)

        if os.path.exists(env_path):
            with open(env_path, 'r') as f: pass
        else:
            utils.debug("Missing credentials file. Creating new credentials file.", level="warning", console=console)
            time.sleep(1)
            with open(env_path, 'w') as f: pass

        utils.clean_env_file()
        dotenv.load_dotenv(env_path)
        required_api_key_queue = []
        for key in utils.SERVICES.keys():
            alias = utils.SERVICES[key]['alias']
            required = utils.SERVICES[key]['required']
            env_value = os.getenv(key)
            if not env_value:
                if required:
                    utils.debug(f"Required service '{alias}' missing! Queued for input.", level="warning", console=console)
                    time.sleep(1)
                    required_api_key_queue.append(key)
            else:
                utils.SERVICES[key]['api_key'] = env_value
    utils.debug("Successfully launched ImagineSuite!", level="success")
    utils.clear_console(1, header=False, console=console)
    return loaded_config, required_api_key_queue if required_api_key_queue != [] else None, new_data

def critical_error(desc):
    utils.clear_console(console=console)
    utils.print("[bold]Critical error occurred![/bold]", level="error", console=console)
    utils.print(f"Developer Info: {desc}", level="debug", console=console)
    utils.print("Restarting ImagineSuite...", console=console)
    time.sleep(3)
    utils.restart()
    
def edit_config(key):
    utils.clear_console(console=console)
    rule = loaded_config[key]
    data_type = type(rule['value'])
    description = rule['description']
    min_value = rule.get("min_value")
    max_value = rule.get("max_value")
    utils.print(f"[bold]Currently editing rule:[/bold] '{key}'.", console=console)
    utils.print(f"[bold]Description:[/bold] {description}", console=console)
    if min_value and max_value: utils.print(f"[bold]Value Range[/bold]: {min_value} - {max_value}")
    elif min_value : utils.print(f"[bold]Minimum Value[/bold]: {min_value}")
    elif max_value: utils.print(f"[bold]Maximum Value[/bold]: {min_value}")
    
    if data_type == int:
        new_value = utils.prompt_input("Enter your new value (enter back to go back)")
        if new_value == "back": return
        try: new_value = int(new_value)
        except:
            utils.print("Please enter an integer.", level='error', console=console)
            time.sleep(2)
            edit_config(key)
            return
        if min_value:               
            if new_value < min_value:
                utils.print("New value is too low for this ruleset.", level='error', console=console)
                time.sleep(2)
                edit_config(key)
                return
        if max_value:
            if new_value > max_value:
                utils.print("New value is too high for this ruleset.", level='error', console=console)
                time.sleep(2)
                edit_config(key)
                return
    elif data_type == float:
        new_value = utils.prompt_input("Enter your new value (enter back to go back)")
        if new_value == "back": return
        try: new_value = float(new_value)
        except:
            utils.print("Please enter a float.", level='error', console=console)
            time.sleep(2)
            edit_config(key)
            return
        if min_value:               
            if new_value < min_value:
                utils.print("New value is too low for this ruleset.", level='error', console=console)
                time.sleep(2)
                edit_config(key)
                return
        if max_value:
            if new_value > max_value:
                utils.print("New value is too high for this ruleset.", level='error', console=console)
                time.sleep(2)
                edit_config(key)
                return
    elif data_type == bool:
        if rule['value']:
            new_value = not utils.confirm_input(f"Do you want to disable '[green]{key}[/green]'")
        else:
            new_value = utils.confirm_input(f"Do you want to enable '[green]{key}[/green]'")
        if new_value == rule['value']: return
    else:
        new_value = utils.prompt_input("Enter your new value (enter back to go back)").strip()
        if new_value == 'back': return
        if len(new_value) < 3:
            utils.print("Values must be a minimum of length 3 for this ruleset.", level='error', console=console)
            time.sleep(2)
            edit_config(key)
            return
    
    if new_value == rule['value']: 
        utils.print("Entered value isn't different from current value!", level='error', console=console)
        time.sleep(2)
        edit_config(key)
        return
    
    new_config, changed = utils.clean_config_file(console=console)
    utils.clear_console(console=console)
    with console.status(f"[bold green] Applying new value for '{key}'...", spinner='point'): time.sleep(2)
    if changed: critical_error("Config file crucially corrupted and has been repaired.")
    else:
        loaded_config[key]['value'] = new_value
        with open(f"{utils.DATA_FOLDER}/config.json", 'w') as f:
            json.dump(loaded_config, f)
        utils.debug(f"Successfully updated configuation rule '{key}'!", level='success', console=console)
        time.sleep(2)
    
def config_menu():
    utils.clear_console(console=console)
    table = Table(title="Configuration Rules", expand=True, title_justify="left")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Rule", style="magenta")
    table.add_column("Description", style="white")
    table.add_column("Minimum Value", style="white", justify="right")
    table.add_column("Maximum Value", style="white", justify="right")
    table.add_column("Value", justify="right", style="green")
    for i, key in enumerate(loaded_config.keys()):
        table.add_row(str(i+1), key, loaded_config[key]['description'], str(loaded_config[key].get('min_value')), str(loaded_config[key].get('max_value')), str(loaded_config[key]['value']))
    utils.print(table, console=console)
    selection = utils.prompt_input("Enter a number for the config rule you want to edit", choices=[str(x+1) for x in range(len(loaded_config.keys()))] + ["back"])
    if selection != "back": edit_config(list(loaded_config.keys())[int(selection)-1])
    else: return
    config_menu()

def verify_key(key, can_quit=False):
    alias = utils.SERVICES[key]['alias']
    description = utils.SERVICES[key]['description']
    if utils.SERVICES[key]['link']:
        description = f"{description} You can get your API key at [link={utils.SERVICES[key]['link']}]{utils.SERVICES[key]['link']}[/link]."
    required_verification = loaded_config['ALWAYS_VERIFY_KEYS']['value'] or utils.SERVICES[key]['always_verify']
    verify = True
    while verify:
        utils.clear_console(console=console)
        utils.print(f"[bold]Currently asking for:[/bold] {alias} API key.", console=console)
        utils.print(f"[bold]Description:[/bold] {description}", console=console)
        if can_quit: api_key = utils.prompt_input(f"Enter your {alias} API key (enter back to go back)").strip()
        else: api_key = utils.prompt_input(f"Enter your {alias} API key").strip()
        if can_quit and api_key == "back": return
        if len(api_key) < 3:
            utils.print("API keys must be a minimum of length 3!", level='error', console=console)
            time.sleep(2)
            verify_key(key, can_quit)
            return
        if not required_verification:
            verify = utils.confirm_input("Would you like to verify the validity of this key")
        if verify:
            utils.clear_console(console=console)
            with console.status(f"[bold green] Verifying {alias} API key...", spinner="point"):
                response = utils.SERVICES[key]['verification_function'](api_key)
                if response == "invalid":
                    utils.debug(f"Oops! The entered {alias} API key was invalid!", level='error', console=console)
                    utils.debug("[bold] Try again!", console=console)
                elif response == "network":
                    utils.debug(f"Oops! We failed to connect to {alias} servers!", level='error', console=console)
                    utils.debug("[bold] Check your internet connection and try again!", console=console)
                else:
                    verify = False
                    utils.debug(f"Successfully validated the {alias} API Key!", level='success', console=console)
            time.sleep(2)
        else:
            utils.clear_console(console=console)
            with console.status(f"[bold green] Continuing without verifying {alias} API key...", spinner="point"): time.sleep(2)
    try:
        utils.SERVICES[key]['api_key'] = api_key
        utils.edit_or_add_env_value(key, api_key)
    except:
        critical_error("Credentials file crucially corrupted or misformated")

def edit_services(required_api_keys=None):
    utils.clear_console(console=console)
    if required_api_keys:
        for i, key in enumerate(required_api_keys):
            utils.clear_console(console=console)
            utils.print(f"You are currently missing {len(required_api_keys)-i} required services(s)!", console=console)
            with console.status(f"[bold green] Loading {utils.SERVICES[key]['alias']} system...", spinner="point"): time.sleep(1)
            verify_key(key)
        utils.clear_console(console=console)
        with console.status("[bold green] You have successfully added all required services! Returning to menu...", spinner="arc"): time.sleep(3)
        utils.clear_console(console=console)
        return
    else:
        available_keys = [key for key in filter(lambda x: utils.SERVICES[x]['api_key'] != None, utils.SERVICES.keys())]
        if len(available_keys) == 0:    
            utils.print("[bold]No added services found![/bold]", level="error")
            utils.print("Missing services can be added in the 'settings/services' menu.")
            utils.prompt_input("Press enter to continue")
            return
        table = Table(title="Editable Services", title_justify="left")
        table.add_column("No.", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("API Key", justify="right", style="green")
        for i, key in enumerate(available_keys):
            table.add_row(str(i+1), utils.SERVICES[key]['alias'], utils.SERVICES[key]['api_key'])
        utils.print(table, console=console)
        selection = utils.prompt_input("Enter a number for the service you want to edit", choices=[str(x+1) for x in range(len(available_keys))] + ["back"])
        if selection == "back": return
        verify_key(list(utils.SERVICES.keys())[int(selection)-1], can_quit=True)
    edit_services(required_api_keys)
        
    
def add_services():
    utils.clear_console(console=console)
    missing_api_keys = []
    for key in utils.SERVICES.keys():
        if not utils.SERVICES[key]['api_key']: missing_api_keys.append(key)
    if missing_api_keys == []:
        table = Table()
        table.add_column("No.", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("API Key", justify="right", style="green")
        for i, key in enumerate(utils.SERVICES.values()):
            table.add_row(str(i+1), key['alias'], key['api_key'])
        utils.print("[bold]No Missing Services![/bold] Here are your available services:", console=console)
        utils.print(table, console=console)
        utils.prompt_input("Press enter to continue")
        return
    else:
        table = Table(title="Missing Services")
        table.add_column("No.", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        for i, key in enumerate(missing_api_keys):
            table.add_row(str(i+1), utils.SERVICES[key]['alias'])
        utils.print(table, console=console)
        selection = utils.prompt_input("Enter a number for the service you want to add", choices=[str(x+1) for x in range(len(missing_api_keys))] + ["back"])
        if selection == "back": return
        verify_key(missing_api_keys[int(selection)-1], can_quit=True)
    add_services()
        
    
def services_menu():
    utils.clear_console(console=console)
    choice = utils.prompt_input("What would you like to do with image generation services?", choices=["add","edit", "back"])
    if choice == "add": add_services()
    if choice == "edit": edit_services()
    if choice == 'back': return
    services_menu()

def update_app_menu():
    utils.clear_console(console=console)
    if not utils.is_exe():
        utils.print("Application information is only available in the .exe!", level='warning', console=console)
        utils.prompt_input("Press enter to continue")
        return
    try: latest = utils.is_latest()
    except: latest = None
    utils.print(f"[bold]Currently running ImagineSuite '{utils.VERSION}'[/bold]")

    if latest == True: 
        utils.print("ImagineSuite is up-to-date!", level="update")
        utils.prompt_input("Press enter to continue")
    elif latest:
        utils.print(f"ImagineSuite {latest} is available!", level="update")
        confirm = utils.confirm_input("Would you like to try update ImagineSuite?")
        if not confirm: return
        utils.clear_console(console=console)
        utils.debug("Attempting to update ImagineSuite.", level="update")
        utils.update_app()
    else:
        utils.print(f"Failed to check for new ImagineSuite versions!", level="warning")
        utils.prompt_input("Press enter to continue")

def settings_menu():
    utils.clear_console(console=console)
    choice = utils.prompt_input("What setting would you like to open?", choices=["config", "services", "app", "back"])
    if choice == "config": config_menu()
    if choice == "services": services_menu()
    if choice == "app": update_app_menu()
    if choice == 'back': return
    settings_menu()

def generate_images(model, prompt, amount, additional_parameters, folder_name, timestamp):
    utils.clear_console(console=console)
    
    batches = [loaded_config['BATCH_SIZE']['value']] * (amount // loaded_config['BATCH_SIZE']['value'])
    if amount % loaded_config['BATCH_SIZE']['value'] != 0: batches.append(amount % loaded_config['BATCH_SIZE']['value'])
    
    os.makedirs(f"{utils.GENERATIONS_FOLDER}/{folder_name}")
    with open(f"{utils.GENERATIONS_FOLDER}/{folder_name}/settings.txt", 'w') as f:
        settings_message = f"Generation Settings\n\nPrompt: {prompt}\nTimestamp: {timestamp}\nModel: {model['alias']}\nImage Amount: {amount}"
        for parameter in additional_parameters.values():
            settings_message += f"\n{parameter['alias']}: {parameter['value']}" 
        f.write(settings_message)
    
    crtical_error_faced = False
    critical_error_desc = None
    image_count = 0
    batches_completed = 0
        
    with console.status(f"[bold green] Generating {amount} image(s) in {len(batches)} batch(es)...", spinner="arc"):
        for result in model['generate_function'](prompt, batches, additional_parameters):
            if result['type'] == "log": 
                utils.clear_console(console=console)
                time.sleep(1)
                utils.debug(result['message'], highlight = False, console=console)
            elif result['type'] == "error":
                if result['level'] == "critical":
                    crtical_error_faced = True
                    critical_error_desc = result['message']
                else:
                    utils.debug("[bold]Handled error faced! Skipping to next batch...[/bold]", level="error", console=console)
                    utils.debug(f"Developer Info: {result['message']}", level="debug", highlight = False, console=console)
                    time.sleep(4)
            elif result['type'] == "b64_json" or result['type'] == "url":
                utils.debug(result['message'], highlight = False, console=console)
                time.sleep(1)
                images = result['value']
                utils.debug(f"Saving {len(images)} image(s)...", highlight = False, console=console)
                time.sleep(2)
                
                images_saved = 0
                for image in images:
                    image_count += 1
                    if result['type'] == "b64_json":
                        try: utils.base64_json_to_image(image, f"{utils.GENERATIONS_FOLDER}/{folder_name}/{image_count}.png")
                        except: 
                            utils.debug(f"Failed to save image {image_count}! Continuing...", highlight = False, level="warning", console=console)
                            time.sleep(2)
                        else: images_saved += 1
                    elif result['type'] == "url":
                        try: utils.url_to_image(image, f"{utils.GENERATIONS_FOLDER}/{folder_name}/{image_count}.png")
                        except: 
                            utils.debug(f"Failed to save image {image_count}! Continuing...", highlight = False, level="warning", console=console)
                            time.sleep(2)
                        else: images_saved += 1
                        
                if images_saved == 0: utils.debug("Failed to save all images! Continuing...", highlight = False, level="warning", console=console)
                else: utils.debug(f"Saved {images_saved} image(s) out of {len(images)}!", highlight = False, level="success", console=console)
                time.sleep(2)
                
                batches_completed += 1
                if batches_completed != len(batches):  
                    utils.clear_console(console=console)
                    utils.debug(f"Waiting {loaded_config['BATCH_TIMEOUT']['value']} second(s) before continuing to the next batch to avoid rate limits.", highlight = False, level="debug", console=console)
                    utils.debug("This value can be changed in the settings/config menu.", highlight = False, console=console)
                    time.sleep(loaded_config['BATCH_TIMEOUT']['value'])
        
            if crtical_error_faced: break
        
    utils.clear_console(console=console)
        
    if crtical_error_faced:
        utils.print("[bold]Critical Error Occured![/bold]", level="error")
        utils.print(f"Description: {critical_error_desc}", level="debug", highlight=False)
        if utils.confirm_input("\nWould you like to delete the generation folder?"):
            utils.clear_console(console=console)
            with console.status("[bold green] Deleting generation folder...", spinner="arc"): time.sleep(1)
            try: shutil.rmtree(f"{utils.GENERATIONS_FOLDER}/{folder_name}")
            except: pass
        return

    utils.print("[bold]Generation finished successfully![/bold]", level="success")
    utils.prompt_input("Press enter to continue")

def generate_model(model):
    utils.clear_console(console=console, check_online=model['online_only'], show_reconnect_info=1)
    if model['online_only'] and not utils.last_known_online:
        utils.print("This model requires an internet connection. Please try again later.", level='error', console=console)
        time.sleep(3)
        return
    parameters = model['additional_parameters']
    utils.print("[bold]Base Parameters for Image Generation[/bold]", console=console)
    prompt = utils.prompt_input("Enter your image generation prompt (enter back to go back)").strip()
    if prompt == "back": return
    if len(prompt) < 3:
        utils.print("Prompt must have a length of at least 3.", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return
    utils.clear_console(console=console)
    utils.print("[bold]Base Parameters for Image Generation[/bold]", console=console)
    image_amount = utils.prompt_input(f"Enter how many images (maximum {loaded_config['MAX_IMAGES']['value']}) to generate (enter back to go back)")
    if image_amount == "back": return
    try: image_amount = int(image_amount)
    except:
        utils.print("Please enter an integer.", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return
    if image_amount not in range(1,loaded_config["MAX_IMAGES"]["value"]+1):
        utils.print(f"Value not in range 1-{loaded_config['MAX_IMAGES']['value']}.", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return  
    utils.clear_console(console=console)
    utils.print("[bold]Base Parameters for Image Generation[/bold]", console=console)
    title = utils.prompt_input("Enter a title for this generation (leave blank for timestamp or enter back to go back)").strip()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    if title == "back": return
    if title == "": title = timestamp
    if len(title) < 3:
        utils.print("Title must have a length of at least 3.", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return
    if os.path.exists(f"{utils.GENERATIONS_FOLDER}/{title}"):
        utils.print("Generation folder with the same title already exists!", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return
    try: os.makedirs(f"{utils.GENERATIONS_FOLDER}/{title}")
    except:
        utils.print("Invalid title! Cannot make folder with entered title.", level='error', console=console)
        time.sleep(2)
        generate_model(model)
        return
    else: os.rmdir(f"{utils.GENERATIONS_FOLDER}/{title}")
    utils.clear_console(console=console)
    with console.status(f"[bold green] Loading {model['alias']} additional parameters...", spinner="point"): time.sleep(2)
    additional_parameters = {}
    if not parameters: 
        with console.status(f"[bold green] No additional parameters found. Continuing...", spinner="point"): time.sleep(2)
    else:
        for parameter in parameters:
            utils.clear_console(console=console)
            utils.print(f"[bold]Currently asking for:[/bold] {parameter['alias']}", console=console)
            utils.print(f"[bold]Description:[/bold] {parameter['description']}", console=console)
            utils.print(f"[bold]Default option:[/bold] {parameter['default']}")
            choice = utils.prompt_input(f"Enter your option for this parameter", choices=parameter['options'] + ['back'])
            if choice == "back": return
            additional_parameters[parameter['name']] = {"alias": parameter['alias'], "value": choice}
        utils.clear_console(console=console)
        with console.status(f"[bold green] Additional parameters applied. Continuing...", spinner="point"): time.sleep(2)
    generate_images(model, prompt, image_amount, additional_parameters, title, timestamp)

def generate_service(service_key):
    utils.clear_console(console=console)
    service = utils.SERVICES[service_key]
    models = service['models']
    table = Table(title=f"Available Models for {service['alias']}", title_justify="left")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Online Only")
    table.add_column("Description", style="green")
    for i, model in enumerate(models):
        table.add_row(str(i+1), model['alias'], str(model['online_only']), model['description'])
    utils.print(table, console=console)
    selection = utils.prompt_input("Enter a number for the model you would like to use", choices=[str(x+1) for x in range(len(models))] + ["back"])
    if selection == "back": return 
    generate_model(models[int(selection)-1])
    generate_service(service_key)


def generate_menu():
    utils.clear_console(console=console)
    available_keys = [key for key in filter(lambda x: utils.SERVICES[x]['api_key'] != None, utils.SERVICES.keys())]
    if len(available_keys) == 0:
        utils.print("[bold]No available image generation services![/bold]", level="error")
        utils.print("Missing services can be added in the 'settings/services menu.")
        utils.prompt_input("Press enter to continue")
        return
    table = Table(title="Available Image Generation Services", title_justify="left")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description")
    table.add_column("Models", style="green")
    for i, key in enumerate(available_keys):
        models = ""
        for model in utils.SERVICES[key]['models']: models += f"{model['alias']}, "
        models = models[:-2]
        table.add_row(str(i+1), utils.SERVICES[key]['alias'], utils.SERVICES[key]['description'], models)
    utils.print(table, console=console)
    if len(available_keys) != len(utils.SERVICES.keys()): utils.print("Missing services can be added in the 'settings/services' menu.")
    selection = utils.prompt_input("Enter a number for the service you would like to use", choices=[str(x+1) for x in range(len(available_keys))] + ["back"])
    if selection == "back": return
    generate_service(list(utils.SERVICES.keys())[int(selection)-1])
    generate_menu()

def view_generation_settings(folder_name):
    utils.clear_console(console=console)
    settings_exists = os.path.exists(f"{utils.GENERATIONS_FOLDER}/{folder_name}/settings.txt")
    if not settings_exists: 
        utils.print("[bold]Settings file not found![/bold]", level="error")
        utils.prompt_input("Press enter to continue")
        return
    with open(f"{utils.GENERATIONS_FOLDER}/{folder_name}/settings.txt", "r") as f: lines = f.readlines()
    for line in lines: utils.print(line.strip(), highlight=False)
    utils.prompt_input("\nPress enter to continue")

def view_folder(folder_name):
    utils.clear_console(console=console)
    if not os.path.exists(f"{utils.GENERATIONS_FOLDER}/{folder_name}"):
        utils.print(f"Folder '{folder_name}' missing! Returning.", level="error")
        time.sleep(2)
        return
    images = [image for image in filter(utils.valid_generation_image, os.listdir(f"{utils.GENERATIONS_FOLDER}/{folder_name}"))]
    if len(images) == 0:
        utils.print("[bold]No images found![/bold]", level="error")
        delete = utils.confirm_input("Would you like to delete this generation folder?")
        if delete:
            utils.clear_console(console=console)
            with console.status("[bold green] Deleting generation folder...", spinner="arc"): time.sleep(2)
            try: shutil.rmtree(f"{utils.GENERATIONS_FOLDER}/{folder_name}")
            except: pass
            return
        else: return
    else:
        utils.print(f"[bold]{len(images)} Image(s) found![/bold]", highlight=False)
    settings_exists = os.path.exists(f"{utils.GENERATIONS_FOLDER}/{folder_name}/settings.txt")
    choices = ["open","delete","back"]
    if not settings_exists: utils.print("Settings file not found!", level="warning")
    else: choices.insert(1, "settings")
    selection = utils.prompt_input(f"What would you like to do with the generation folder?", choices=choices)
    if selection == "open": webbrowser.open(f'file:///{utils.get_working_dir_path()}/{utils.GENERATIONS_FOLDER}/{folder_name}', new=1, autoraise=True)
    elif selection == "settings": view_generation_settings(folder_name)
    elif selection == "delete":
        utils.clear_console(console=console)
        delete = utils.confirm_input("Would you like to delete this generation folder?")
        if delete:
            utils.clear_console(console=console)
            with console.status("[bold green] Deleting generation folder...", spinner="arc"): time.sleep(1)
            try: shutil.rmtree(f"{utils.GENERATIONS_FOLDER}/{folder_name}")
            except: pass
            return
    elif selection == "back": return
    view_folder(folder_name)

def view_menu():
    utils.clear_console(console=console)
    if not os.path.exists(utils.GENERATIONS_FOLDER):
        with console.status("[bold green] Generations folder missing. Creating new generations folder...", spinner="arc"): time.sleep(2)
        os.mkdir(utils.GENERATIONS_FOLDER)
    table = Table(title="Available Generations", title_justify="left")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Name", style="magenta")
    folders = [folder for folder in filter(lambda x: x.count('.') == 0, os.listdir(utils.GENERATIONS_FOLDER))]
    if len(folders) == 0:
        utils.print("[bold]No Generations found![/bold]")
        utils.prompt_input("Press enter to continue")
        return
    for i, folder in enumerate(folders):
        table.add_row(str(i+1), folder)
    utils.print(table, console=console)
    selection = utils.prompt_input("Enter a number for the generation you would like to view", choices=[str(x+1) for x in range(len(folders))] + ["back"])
    if selection == "back": return
    view_folder(folders[int(selection)-1])
    view_menu()

def home(attempt_reconnect=True):
    utils.clear_console(console=console, check_online=attempt_reconnect, show_reconnect_info=2)
    if new_data: utils.print("[bold]Hi there![/bold] Welcome to [bold cyan]ImagineSuite![/bold cyan]", console=console)
    else: utils.print("[bold]Nice to see you again![/bold] Welcome back to [bold cyan]ImagineSuite![/bold cyan]", console=console)
    choices = ["generate", "view", "settings", "restart", "quit"]
    if not utils.last_known_online: choices.insert(2, "reconnect")
    choice = utils.prompt_input(f"What's next [bold]{utils.get_user_name()}[/bold]?", choices=["generate", "view", "settings", "restart", "quit"])
    if choice == "generate" : generate_menu()
    if choice == "view": view_menu()
    if choice == "reconnect":
        home()
        return
    if choice == "settings": settings_menu()
    if choice == "restart":
        utils.clear_console(console=console)
        if utils.is_exe():
            confirm = utils.confirm_input("Are you sure you want to restart ImagineSuite")
            if confirm: utils.restart()
        else:
            utils.print("Restarting the app isn't available when running the Python script!", level="warning")
            time.sleep(2)       
    if choice == "quit":
        confirm = utils.confirm_input("Are you sure you want to quit ImagineSuite")
        if confirm: return
    home()

def main():
    global loaded_config, new_data
    loaded_config, required_api_key_queue, new_data = initialise_data()
    utils.print_header()
    if required_api_key_queue:
        utils.print("[bold]Uh oh![/bold] It looks like we're missing some required services. Let's go fix that!", level='warning', console=console)
        with console.status("[bold green] Loading service verifier...", spinner="arc"): time.sleep(5)
        edit_services(required_api_key_queue)
    home(attempt_reconnect=False)
    utils.clear_console()
    with console.status("[bold green] Quitting...", spinner="arc"): time.sleep(2)
    utils.clear_console(header=False)
    sys.exit()

main()