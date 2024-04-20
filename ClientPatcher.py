#!/usr/bin/env python3

import sys, os

def findKeys(d, findStart, GameIDstringBytes, ApiKeys, DesSecrets):
    found = False
    while True:
        keyStart = d.find(GameIDstringBytes + b'\x00', findStart)
        if keyStart < 0:
            break
        apiKeyStart = keyStart + len(GameIDstringBytes)
        while d[apiKeyStart] != 0x24:
            apiKeyStart += 1
        apiKeyStart += 4
        isOK = True
        for i in [8, 13, 18, 23, 48, 53, 58, 63]:
            if d[apiKeyStart+i] != 0x2d:
                isOK = False
                break
        if not isOK:
            findStart = apiKeyStart
            continue
        desSecretStart = apiKeyStart + 0x24 + 4
        findStart = desSecretStart + 0x24
        found = True
        if ApiKeys is not None:
            ApiKeys.append(apiKeyStart)
        if DesSecrets is not None:
            DesSecrets.append(desSecretStart)
    return found

def findURLs(d, findStart, findEnd, URLs):
    found = False
    while True:
        urlStart = d.find(b'\x00\x00\x00http', findStart)
        if urlStart < 0 or urlStart > findEnd:
            break
        urlLen = d[urlStart-1]
        findStart = urlStart + urlLen
        urlStart += 3 # because prefix b'\x00\x00\x00' in find
        URLs.append((urlStart, urlLen))
        found = True
    return found

def overrideSubstring(instr, startpos, replstr):
    return instr[:startpos] + replstr + instr[startpos+len(replstr):]

def edit(resourcesAssetsFile, NewURL, GameIDstring = None, NewApiKey = None, MakeBackup = True):
    ApiKeys = []
    DesSecrets = []
    URLs = []

    # initial check
    
    if not NewURL.startswith('http'):
        raise RuntimeError(f"NewURL ({NewURL}) should start with 'http'")

    if MakeBackup and not os.path.isfile(resourcesAssetsFile + ".ClientPatcher.bck"):
        with open(resourcesAssetsFile, 'rb') as src, open(resourcesAssetsFile + ".ClientPatcher.bck", 'wb') as dst: dst.write(src.read())

    # open resources.assets file

    f = open(resourcesAssetsFile, 'br+')
    d = f.read()

    # find ProductSettings and detect game

    ProductSettings = d.find(b'ProductSettings')
    if ProductSettings < 0:
        raise RuntimeError(f"Not found ProductSettings in {resourcesAssetsFile}")

    if GameIDstring is None:
        GameIDstringIsAutodetected = True
        for x in [b'SOD Windows standalone', b'JSMythies windows', b'MathBlaster Windows Standalone', b'MainStreet']:
            if d.find(x, ProductSettings) > 0:
                GameIDstring = x.decode()
                GameIDstringBytes = x
                break
        if GameIDstring is None:
            raise RuntimeError(f"Autodetect of GameIDstring didn't work  ... GameIDstring can't be None")
    else:
        GameIDstringIsAutodetected = False
        GameIDstringBytes = GameIDstring.encode()

    # find positions of editable values

    if not findKeys(d, ProductSettings, GameIDstringBytes, ApiKeys, DesSecrets):
        raise RuntimeError(f"Not found API keys for {GameIDstring} in {resourcesAssetsFile}")
    
    if not findURLs(d, ProductSettings, ApiKeys[0], URLs):
        raise RuntimeError(f"Not found URLs in {resourcesAssetsFile}")

    # get version info

    Version = DesSecrets[0] + 0x24 + 4
    VersionInfo = d[Version:Version+6].strip(b'\x00').decode().split('.')
    VersionInfo = [int(x) for x in VersionInfo]

    print(f"Editing '{GameIDstring}' {VersionInfo}")

    # for autodetected SoD 3.31.0 find positions of extra info to update:

    if GameIDstringIsAutodetected and GameIDstring == 'SOD Windows standalone' and VersionInfo == [3, 31, 0]:
        # - DesSecrets for Android
        if not findKeys(d, ProductSettings, b'Dragons Google', None, DesSecrets):
            raise RuntimeError(f"Not found Android DesSecret")
        # - DesSecrets for iOS
        if not findKeys(d, ProductSettings, b'Dragons iOS', None, DesSecrets):
            raise RuntimeError(f"Not found iOS DesSecret")
        # - ApiKeys and DesSecrets for Steam
        if not findKeys(d, ProductSettings, b'Dragons Steam Windows', ApiKeys, DesSecrets):
            raise RuntimeError(f"Not found iOS DesSecret")

    # check url length

    shortestURL = [None, len(d)]
    for u in URLs:
        if u[1] < shortestURL[1]:
            shortestURL = u
    if shortestURL[1] < len(NewURL):
        u = shortestURL[0]
        raise RuntimeError(f"New URL is longer that maximum length = {shortestURL[1]} (for current value: {d[shortestURL[0]:shortestURL[0]+shortestURL[1]]})")

    # prepare new values

    if not NewApiKey:
        if GameIDstring.startswith("SOD") or GameIDstring.startswith("Dragons") or GameIDstring.startswith("DWDragons"):
            if VersionInfo == [3, 31, 0]:
                NewApiKey = "B99F695C-7C6E-4E9B-B0F7-22034D799013"
            else:
                NewApiKey = f'A{VersionInfo[0]}A{VersionInfo[1]:02}A{VersionInfo[2]}A-7C6E-4E9B-B0F7-22034D799013'
        elif GameIDstring.startswith("JSMythies"):
            NewApiKey = "E20150CC-FF70-435C-90FD-341DC9161CC3"
        elif GameIDstring.startswith("MathBlaster"):
            NewApiKey = "6738196d-2a2c-4ef8-9b6e-1252c6ec7325"
        elif GameIDstring.startswith("MainStreet"):
            if VersionInfo[0] == 1 and VersionInfo[1] > 2:
                NewApiKey = "15A1A21A-4A95-46F5-80E2-58574DA65875"
            else:
                NewApiKey = "1552008F-4A95-46F5-80E2-58574DA65875"
        else:
            raise RuntimeError(f"Autodetect of NewApiKey didn't work ... NewApiKey can't be None")

    if len(NewApiKey) != 0x24:
        raise RuntimeError(f"Invalid length of new apiKey: {NewApiKey}")

    NewDesSecret = b'56BB211B-CF06-48E1-9C1D-E40B5173D759'

    # update values

    for u in URLs:
        x = u[1] - len(NewURL)
        d = overrideSubstring(d, u[0], NewURL.encode() + b'\x00' * x)
    for x in ApiKeys:
        d = overrideSubstring(d, x, NewApiKey.encode())
    for x in DesSecrets:
        d = overrideSubstring(d, x, NewDesSecret)

    # write updated file

    f.seek(0)
    f.write(d)
    f.close()

def runGui():
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import filedialog
    import json
    
    root = tk.Tk()
    
    settings = {'bg': "#1e1e1e", 'fg': "white"}
    
    root.title("SoDOff Server Selector")
    root.configure(bg=settings['bg'])
    def center_window(window, width, height):
        x_coordinate = int((window.winfo_screenwidth() - width) / 2)
        y_coordinate = int((window.winfo_screenheight() - height) / 2)
        window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")
    center_window(root, 720, 230)
    
    root.grid_columnconfigure((0, 1, 2), weight=1)
    
    # Title and subtitle
    title_label = tk.Label(root, text="SoDOff Server Selector", font=("Arial", 14), **settings)
    title_label.grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="n")
    
    version_label = tk.Label(root, text="Please choose predefined server or enter URL", font=("Arial", 10, "italic"), **settings)
    version_label.grid(row=1, column=0, columnspan=3, sticky="n")
    
    try:
        servers_list_file = __file__.rsplit('.', 1)[0] + '.json'
        if os.path.isfile(servers_list_file):
            servers = json.load(open(servers_list_file))
        else:
            servers = json.load(open(os.path.basename(servers_list_file)))
    except Exception as err:
        print(f"Can't load server list from config file {servers_list_file}: err")
        servers = {
            'SoD - localhost': 'http://localhost:5001/.com/DWADragonsUnity/',
        }
    
    server = tk.StringVar(root)
    server.set("select")  # Default value
    
    def select_predef_server(event):
        nonlocal server, url_input
        x = servers.get(server.get(), "")
        if x != "":
            url_input.delete("1.0",tk.END)
            url_input.insert("end", x)
    
    client_path = None
    
    server_dropdown = ttk.Combobox(root, textvariable=server, values=list(servers.keys()), state="readonly", width=20)
    server_dropdown.grid(row=2, column=0, columnspan=1, pady=(5,10))
    server_dropdown.bind('<<ComboboxSelected>>', select_predef_server)
    
    url_input = tk.Text(root, height = 1, width = 43) 
    url_input.grid(row=2, column=1, columnspan=2, pady=(5,10))
    
    destination_label = tk.Label(root, text="Please choose client folder", font=("Arial", 10, "italic"), **settings)
    destination_label.grid(row=4, column=0, columnspan=3, sticky="n")
    
    def select_server_directory():
        nonlocal client_path
        client_path = filedialog.askopenfile(title = "Select resources.assets or JS game exe file", filetypes=[
            ("default", "resources.assets *Main.exe 6eb4ac313b3875249a8c684d320f337f"), # 6eb4ac313b3875249a8c684d320f337f is SoD Android
            ("all", "*"),
        ])
        if client_path:
            client_path = client_path.name
        destination_input.configure(text=client_path)
            
    destination_input = tk.Button(root, height=1, width=60, command=select_server_directory, text="")
    destination_input.grid(row=5, column=0, columnspan=3, pady=(5,10))
    
    def patch_client():
        nonlocal client_path, url_input
        if client_path.endswith(".exe"):
            client_path = os.path.dirname(client_path) + "/" + os.path.basename(client_path).rsplit(".", 1)[0] + "_Data/resources.assets"
            if not os.path.isfile(client_path):
                messagebox.showerror("Error", "Can't find resources.assets based on selected .exe file.\n\nTry select resources.assets directly.")
                return
        try:
            url = url_input.get(1.0, "end-1c")
            edit(client_path, url, MakeBackup = not client_path.endswith("/assets/bin/Data/6eb4ac313b3875249a8c684d320f337f"))
        except Exception as err:
            messagebox.showerror("Error", str(err))
            return
        messagebox.showinfo("Patch Complete", f"Client was successfully patched to use: {url}")
    
    patch_button = tk.Button(root, text="Patch client", command=patch_client, **settings)
    patch_button.grid(row=6, column=2, pady=(20,10), padx=(110,0))
    
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} inputfile newURL [GameIDstring apiKey]")
        runGui()
    else:
        if len(sys.argv) > 4:
            edit(*sys.argv[1:5])
        else:
            edit(*sys.argv[1:3])
