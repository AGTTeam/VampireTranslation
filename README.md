# Vampire Translation
This repository is for the tool used to translate the game. If you're looking for the English patch, click [here](https://agtteam.net/vampire).  
## Setup
Install [Python 3](https://www.python.org/downloads/).  
Download this repository by downloading and extracting it, or cloning it.  
Copy the original Japanese rom into the same folder and rename it as `vampire.nds`.  
Run `run_windows.bat` (for Windows) or `run_bash` (for OSX/Linux) to run the tool.  
## Font Editing
Copy `font_output.png` to `font_input.png` and edit it.  
The glyphs should be in the same order as the `fontconfig.txt` file, where you should also specify the glyph size.  
To fit more characters in text lines, the tool supports a simple dictionary compression where any sentence or word can be shortened to 2 bytes.  
You can add words at the bottom of the file and not specify any length after the `=` sign. Longer words should come first.  
Limitations: no codes like `<name>`, and up to a maximum of 240 words.  
Format example (set A and B to 5 pixels of width, add "something" "Day Class" and "Day" to the dictionary):
```
A=5
B=5
something=
Day Class=
Day=
```
## Text Editing
Rename the \*\_output.txt files to \*\_input.txt (bin_output.txt to bin_input.txt, etc) and add translations for each line after the `=` sign.  
The text in wsb_input is automatically wordwrapped, but a `|` can be used to force a line break.  
The `>>` can be used at the start of strings that need to avoid using the dictionary feature, for example character names.  
Control codes are specified as `<XX>`, they should usually be kept.  
Comments can be added at the end of lines by using `#`.  
## Image Editing
Rename the out\_\* folders to work\_\* (out_IMG to work_IMG, etc).  
Edit the images in the work folder(s). The palette on the right should be followed but the repacker will try to approximate other colors to the closest one.  
If an image doesn't require repacking, it should be deleted from the work folder.  
## Run from command line
This is not recommended if you're not familiar with Python and the command line.  
After following the Setup section, run `pipenv sync` to install dependencies.  
Run `pipenv run python tool.py extract` to extract everything, and `pipenv run python tool.py repack` to repack.  
You can use switches like `pipenv run python tool.py repack --bin` to only repack certain parts to speed up the process.  
