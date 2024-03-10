# ImagineSuite

A Rich CLI-based application/script to easily generate AI images using multiple services.

## Features
- Asynchronous image generation in batches
- Image/prompt saving and management
- Service and authentication management
- Configurable settings for generation
- Easy framework to add new generation services (`utils.py`)
- Robust error and file handling

## Usage

There are 3 options to use the application:

- Running the pre-compiled exe file (Recommended)
- Running the script directly
- Running your own self-compiled exe file

### Running the pre-compiled exe file (Recommended)
> [!WARNING]  
> The .exe can be labeled as potentially dangerous/malitious. Run at your own discretion.

Go to the releases tab and find the latest release and download the .zip file. It will contain the latest pre-compiled .exe file.

Simply run the .exe file.

### Running the script directly

Clone the repository:
```bash
git clone https://github.com/TheNebulo/ImagineSuite.git
```

Install requirements
```bash
pip install requirements.txt
```

Run the script
```bash
python main.py
```

### Running your own self-compiled exe file

> [!IMPORTANT]  
> Self compiling exe's requires minimal experience with the libraries used.

Clone the repository:
```bash
git clone https://github.com/TheNebulo/ImagineSuite.git
```

Install requirements
```bash
pip install requirements.txt
```

Install PyInstaller
```bash
pip install PyInstaller
```

Run the initial compile
```bash
python -m PyInstaller --onefile app.py
```

You will then find a file called `app.exe` in a folder called `/dist`. That's the compiled exe!

The app.spec file will contain the configuration for the compilation process, and if you want to make changes, you can recompile using:
```bash
python -m PyInstaller app.spec
```

More information can be found on official PyInstaller channels.

## License

This code is available with the [GPL 3.0 License](https://choosealicense.com/licenses/gpl-3.0/).