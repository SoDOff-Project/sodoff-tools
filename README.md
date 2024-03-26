# SoDOff - tools

This repo contains auxiliary tools for SoDOff server:

* ClientPatcher - tool for change server address in client binaries
* AssetsDownloader - tool for download assets


## ClientPatcher

* allow change server address in client binaries
  - support for customizable servers list
* support auto detection of game and game version
* change api key and 3des secret also
  - 3des is hard coded to value used by SoDOff api server
  - api key will be set automatically based on detected game (or can be specified in command line mode)

## AssetsDownloader

* GUI and cmd line interface
* support for get configuration from download server
* support for download from raw file list and url prefix (command line only, slow download mode)
  - can be used to download from external sources like archive.org
  - see "Path list mode" below
* checksum based update mode
* download can be stopped and resumed at any time
  - "Stop" stop download after end of downloading current file in progress
  - "Force Stop" stop immediately (not finished files progress will be lost).
* support for server-side mods download and installation
* for command line options info run `./AssetsDownloader.py --help`

### Path list mode

Command line options allow bulk download all paths from file specified via `--path-list` from base url specified via `--url-prefix`.
For example from archive.org: 

```./AssetsDownloader.py --url-prefix https://web.archive.org/web/20230713000000id_/https://s3.amazonaws.com/origin.ka.cdn/ --path-list path_list.txt```

`path_list.txt` should contain one (related to `url-prefix`) path per line, for example:

```
DWADragonsUnity/WIN/3.31.0/High/dwadragonsmain
DWADragonsUnity/WIN/3.31.0/High/data/pfsanctuarydatado
```

Path list can be obtained from `https://web.archive.org/cdx/search/cdx?output=json&fl=original&collapse=urlkey&matchType=prefix&url=s3.amazonaws.com/origin.ka.cdn/DWADragonsUnity/WIN/${Version}/${Quality}/` where `${Version}` should be replaced by version (e.g. `3.31.0`) and `${Quality}` by `Low`, `Mid` or `High`.

## Build and run

### How to run

1. install [Python](https://www.python.org/) with tcl/tk and (AssetsDownloader only) [requests](https://pypi.org/project/requests/) lib
2. run selected script with python (`python3 ClientPatcher.py` or `python3 AssetsDownloader.py`)

### How to create exe file

1. install [Python](https://www.python.org/) with tcl/tk and (AssetsDownloader only) [requests](https://pypi.org/project/requests/) lib
2. install [pyinstaller](https://pypi.org/project/pyinstaller/)
3. run `pyinstaller -F ClientPatcher.py` or `pyinstaller -F AssetsDownloader.py`

Notes:

* while creating exe for `AssetsDownloader.py` you may want to specify `dafault_server_config` (inside python script) value to url to server configuration json file on your asset server

#### How to create Windows exe from Linux

1. install wine
2. install windows version of [Python](https://www.python.org/) under wine:
	`wine python-3.8.10.exe`
3. install dependencies and pyinstaller under windows version of python:
	`wine ~/.wine/drive_c/users/rrp/AppData/Local/Programs/Python/Python38-32/python.exe -m pip install requests pyinstaller`
4. run pyinstaller under wine:
	`wine ~/.wine/drive_c/users/rrp/AppData/Local/Programs/Python/Python38-32/Scripts/pyinstaller.exe -F ClientPatcher.py`
	or
	`wine ~/.wine/drive_c/users/rrp/AppData/Local/Programs/Python/Python38-32/Scripts/pyinstaller.exe -F AssetsDownloader.py`
