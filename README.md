# Vampire Translation
## Setup
Create a "data" folder and copy the rom as "vampire.nds" in it.  
## Run from binary
Download the latest [release](https://github.com/Illidanz/VampireTranslation/releases) outside the data folder.  
Run `tool extract` to extract everything and `tool repack` to repack after editing.  
Run `tool extract --help` or `tool repack --help` for more info.  
## Run from source
Install [Python 3.8](https://www.python.org/downloads/) and pipenv.  
Download [ndstool.exe](https://www.darkfader.net/ds/files/ndstool.exe).  
Download [armips.exe](https://github.com/Kingcom/armips/releases).  
Download xdelta.exe.  
Run `pipenv install`.  
Run the tool with `pipenv run tool.py` or build with `pipenv run pyinstaller tool.spec`.  
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
