#!/usr/bin/env python3

# to install dependencies run: `pip install requests`

dafault_server_config = "Assets_Downloader.json" 

# dafault_server_config can be:
#   - python directory
#   - local path to json file
#   - url to json file
#
# dafault_server_config = {
#     "server": "SERVER BASE URL",
#     "title": "GUI WINDOWS TITLE",
#     "title_label": "GUI WINDOWS MESSAGE",
#     "parallel": NUMBER OF PARALLEL DOWNLOADS
#     "versions": {
#         "3.31 PC High": "DWADragonsUnity/WIN/3.31.0/High",
#         "Content": "DWADragonsUnity/Content",
#         "Mods": "DWADragonsUnity/Mods"
#     }
# }

import sys, time, os, io
import requests
import hashlib
import random, string
from urllib.parse import urlparse
from multiprocessing import Pool, Process, freeze_support
from multiprocessing.managers import SyncManager

class DownloadLog:
    def __init__(self, config, path, file_no = None):
        self.config = config
        if file_no:
            self.file_info = f"{file_no}/{config.total_files} {path}"
        else:
            self.file_info = path
        if config.show_progress:
            self.start_end = ""
            self.end_info = ""
        else:
            self.start_end = "\n"
            self.end_info = self.file_info
    
    def Print(self, msg, start, end):
        with self.config.print_lock:
            print(start + msg + end, end="")
            sys.stdout.flush()
        
    def Start(self, err_count = None):
        self.Print(f"{self.file_info} (err_count={err_count})", start="", end=self.start_end)
    
    def Progress(self, err_count, progress):
        if self.config.show_progress:
            self.Print(f"{self.file_info} {progress}% (err_count={err_count})", start="\r", end="")
    
    def Done(self):
        self.Print(f"{self.end_info} ... done", start="", end="\n")
    
    def Error(self, msg):
        self.Print(f"{self.end_info} ... error: {msg}", start="", end="\n")

class DownloadLogStorage(DownloadLog):
    def __init__(self, config, path, file_no = None):
        super().__init__(config, path, file_no)
        self.log_data = config.Get('log_data')
        self.end_info = self.file_info
    
    def Print(self, msg, start, end):
        if start == "" and end == "\n":
            # write line to final log
            with self.config.print_lock:
                self.log_data['full_log'] += msg + "\n"
                self.log_data[os.getpid()] = ""
                print(msg)
        else:
            with self.config.print_lock:
                self.log_data[os.getpid()] = msg

class DownloadSettings:
    def __init__(self, **args):
        class FakeLock:
            def __enter__(self): return self
            def __exit__(self, *_): pass

        self.block_size = 4096
        self.update_mode = False
        self.urlprefix = ""
        self.localprefix = "assets-cache/"
        self.altlocalprefix = "assets/"
        
        # parallelism and download speed
        self.parallel = 0
        self.run_async = False # when True allow exit from downloadAssets() before download end
        self.sleep_time = 2
        self.err_sleep_time = 10
        
        # max errors
        self.max_retry_count = 5
        self.max_subsequent_failures = 5
        
        # external stop
        self.stop_downloads = False
        self.force_stop_downloads = False
        
        # stop on error
        self.current_errors_count = 0
        self.exit_on_failures = False
        self.failures_files_count = 0
        self.failures_count_lock = FakeLock()
        
        # logs
        self.log_system = DownloadLog
        self.show_progress = True
        self.total_files = "?"
        self.print_lock = FakeLock()

        # adjust default setting using setting from args
        if args.get('parallel', 0) > 0:
            self.sleep_time = 0
            self.show_progress = False
        
        # apply settings from args
        self.__dict__.update(args)

    
    def Error(self):
        with self.failures_count_lock:
            self.failures_files_count += 1
            self.current_errors_count += 1
        return False
    
    def Sucess(self):
        with self.failures_count_lock:
            if self.current_errors_count > 0:
                self.current_errors_count -= 1
        return True
    
    def CanDownload(self):
        if self.stop_downloads:
            self.failures_files_count += 1
            return False
        if self.max_subsequent_failures is not None and self.current_errors_count > self.max_subsequent_failures:
            self.exit_on_failures = True
            return False
        return True
    
    def Get(self, key):
        return self.__dict__[key]
    
    def Set(self, key, val):
        self.__dict__[key] = val
    
    def GetLog(self, **args):
        return self.log_system(self, **args)

class DownloadManager(SyncManager): pass
DownloadManager.register('DownloadSettings', DownloadSettings)

class Parallel:
    def __init__(self, **args):
        if args.get('parallel', 0) == 0:
            self.manager = None
            args['log_data'] = {'full_log': ''}
            self.config = DownloadSettings(**args)
            self.pool = None
        else:
            self.manager = DownloadManager()
            self.manager.start()
            args['failures_count_lock'] = self.manager.Lock()
            args['print_lock'] = self.manager.Lock()
            args['log_data'] = self.manager.dict()
            args['log_data']['full_log'] = ""
            self.config = self.manager.DownloadSettings(**args)
            self.pool = Pool(self.config.Get('parallel'))
    
    def __del__(self):
        if self.manager:
            self.manager.shutdown()
            self.manager = None

class HTTPError(ConnectionError): pass
class ResponseReadError(ConnectionError): pass
    
def downloadFile(
    remote_path,
    local_path,
    config = DownloadSettings(),
    log_path = None,
    log_file_no = None
):
    if not config.CanDownload():
        return None
    
    if log_path is None:
        log_path = local_path
    log = config.GetLog(path=log_path, file_no=log_file_no)
    
    err_count = 0
    while err_count < config.Get('max_retry_count'):
        log.Start(err_count)
        try:
            start_time = time.time()
            response = requests.get(remote_path, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', -1))
                if total_size < 0:
                    raise HTTPError("no content-length in response")
                
                write_path = local_path + ''.join(random.choices(string.ascii_letters, k=6)) + ".tmp"
                with open(write_path, "wb") as file:
                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=config.Get('block_size')):
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size/total_size*100)
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        download_speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                        log.Progress(err_count, progress)
                        if config.Get('force_stop_downloads'):
                            raise ResponseReadError("forced stop downloading")
                
                if downloaded_size < total_size:
                    raise ResponseReadError("response too short")
                else:
                    try:
                        os.rename(write_path, local_path)
                    except:
                        os.replace(write_path, local_path)
                    log.Done()
                    return config.Sucess()
            else:
                raise HTTPError(f"http code {response.status_code}")
        except Exception as err:
            log.Error(err)
            if os.path.exists(local_path):
                os.remove(local_path) # TODO resume download
            if isinstance(err, (HTTPError, ResponseReadError)):
                return config.Error()
            err_count += 1
            time.sleep(config.Get('err_sleep_time')*(err_count**2))
    return config.Error()

def getDownloadResults(arg, config = None):
    if isinstance(arg, Parallel):
        if arg.pool:
            arg.pool.close()
            arg.pool.join()
        arg = arg.config
    if config is None:
        config = arg
    
    if config.Get('sleep_time') > 0:
        time.sleep(config.Get('sleep_time'))
    
    if config.Get('exit_on_failures'):
        return (1, "Too many errors -> exit")
    
    if config.Get('failures_files_count') > 0:
        return (2, "Some files are missed - rerun to try redownload")
    
    return (0, "Downloaded all files")

def downloadAssets(
    paths, 
    config = DownloadSettings(),
    parallel = None,
):
    def FileIsOK(path, checksum = None):
        if not os.path.exists(path):
            return False
        if checksum is None:
            return True
        with open(path, "rb") as file:
            try:
                file_checksum = hashlib.file_digest(file, "md5").hexdigest()
            except: # for Python < 3.11
                file_hash = hashlib.md5()
                while chunk := file.read(131072):
                    file_hash.update(chunk)
                file_checksum = file_hash.hexdigest()
        return checksum == file_checksum
    
    if isinstance(paths, io.TextIOWrapper):
        paths = paths.read()
    
    if isinstance(paths, str):
        paths = paths.split('\n')
    
    config.Set('total_files', len(paths))
    
    file_no = 0
    for path in paths:
        file_no += 1
        
        path = path.strip()
        if path == "":
            continue
        
        if not isinstance(path, str):
            path, checksum = path[0], path[1]
        elif config.Get('update_mode'):
            path = path.split("  ", 1)
            path, checksum = path[1], path[0]
        else:
            checksum = None
        
        path = path.strip()
        remote_path = config.Get('urlprefix') + path
        local_path = config.Get('localprefix') + path
        
        # check if file exist in local destination path (e.g. assets-cache)
        if FileIsOK(local_path, checksum):
            continue;
        
        # check if file exist in alternative local path (e.g. assets)
        if config.Get('altlocalprefix') is not None and FileIsOK(config.Get('altlocalprefix') + path, checksum):
            continue;
        
        dir_path = os.path.dirname(local_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        
        if parallel and parallel.pool:
            parallel.pool.apply_async(
                downloadFile,
                args=(remote_path, local_path, config, path, file_no)
            )
        else:
            downloadFile(remote_path, local_path, config, path, file_no)
            getDownloadResults(config)
            
    if parallel and parallel.pool and config.Get('run_async'):
        return (-1, "Please call getDownloadResults(returned_value[2]) for results", parallel)
    
    return getDownloadResults(parallel, config)


def getServerConfig(server_config):
    if isinstance(server_config, dict):
        return server_config
    
    import json
    if urlparse(server_config).scheme == "":
        return json.load(open(server_config))
    
    response = requests.get(server_config)
    if response.status_code != 200:
        raise BaseException("Error while downloading config.")
    
    return json.loads(response.text)

def getAssetList(path, config):
    log = config.GetLog(path="asset list")
    log.Start()
    
    if config.Get('update_mode'):
        url = config.Get('urlprefix') + path + ".update"
    else:
        url = config.Get('urlprefix') + path + ".list"
    
    response = requests.get(url)
    if response.status_code != 200:
        return(3, "Error while downloading assets list.")
    
    log.Done()
    
    return response.text

def runDownloadFromConfig(server_config, list_name, update_mode, log_system=DownloadLog):
    parallel = int(server_config["parallel"])
    if parallel > 1:
        parallel = Parallel(parallel=parallel, run_async=True, update_mode=update_mode, urlprefix=server_config["server"], log_system=log_system)
        runconfig = parallel.config
    else:
        parallel = None
        runconfig = DownloadSettings(sleep_time=server_config.get("sleep_time", 0), update_mode=update_mode, urlprefix=server_config["server"])
    
    if "dst" in server_config["versions"][list_name]:
        runconfig.Set("localprefix", server_config["versions"][list_name]["dst"])
        runconfig.Set("altlocalprefix", None)
    
    asset_list = getAssetList(server_config["versions"][list_name]["src"], runconfig)
    downloadAssets(asset_list, runconfig, parallel)
    
    return parallel


def runGui(server_config):
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    from tkinter import scrolledtext
    from tkinter import filedialog
    root = tk.Tk()
    
    guisettings = {'bg': "#1e1e1e", 'fg': "white"}
    
    root.title("Assets Downloader ... loading configuration")
    root.configure(bg=guisettings['bg'])
    def center_window(window, width, height):
        x_coordinate = int((window.winfo_screenwidth() - width) / 2)
        y_coordinate = int((window.winfo_screenheight() - height) / 2)
        window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")
    center_window(root, 930, 400)
    
    root.grid_columnconfigure((0, 1, 2, 3, 4 ,5), weight=1)
    
    title_label_text = tk.StringVar(root)
    title_label_text.set("Please wait for download configuration")
    title_label = tk.Label(root, textvariable=title_label_text, font=("Arial", 14), **guisettings)
    title_label.grid(row=0, column=0, columnspan=6, pady=(10, 5), sticky="n")
    
    root.update()
    
    try:
        server_config = getServerConfig(server_config)
    except:
        messagebox.showerror("Error", "Can't download configuration.")
        return 5
    
    root.title(server_config["title"])
    title_label_text.set(server_config["title_label"])
    
    version = tk.StringVar(root)
    version.set("select")  # Default value

    destination_path = None
    parallel = None
    
    def download_assets(update):
        nonlocal version, destination_path, parallel, root, log_output
        if parallel is not None:
            return
        
        ver = version.get()
        if not ver in server_config["versions"] or not "src" in server_config["versions"][ver]:
            messagebox.showerror("Error", "Select version!")
            return
        
        if destination_path is None:
            messagebox.showerror("Error", "Select the directory containing the SoDOff server!")
            return
        
        log_output.insert("end", "Initializing ... please wait\n")
        root.update()
        
        os.chdir(destination_path)
        parallel = runDownloadFromConfig(server_config, ver, update, DownloadLogStorage)
        
        while not parallel.pool._inqueue.empty():
            log_data = dict(parallel.config.Get('log_data'))
            text = log_data['full_log']
            for k in log_data:
                if k != 'full_log':
                    if log_data[k] != "":
                        text += log_data[k] + "\n"

            log_output.delete("1.0",tk.END)
            log_output.insert("end", text)
            log_output.see(tk.END)
            root.update()
            time.sleep(0.2)
        ret = getDownloadResults(parallel)
        log_output.insert("end", ret[1]+"\n")
        if ret[0]:
            messagebox.showerror("Error", ret[1])
        else:
            messagebox.showinfo("Download Complete", ret[1])
        
        parallel = None
    
    def stop_download_assets():
        nonlocal parallel
        if parallel:
            parallel.config.Set('stop_downloads', True)
    
    def force_stop_download_assets():
        nonlocal parallel
        if parallel:
            parallel.config.Set('stop_downloads', True)
            parallel.config.Set('force_stop_downloads', True)
    
    def select_server_directory():
        nonlocal destination_path
        destination_path = filedialog.askdirectory(title = "Select SoDOff server directory")
        if (not os.path.exists(destination_path + "/sodoff") \
            and not os.path.exists(destination_path + "/sodoff.exe") \
            and not os.path.exists(destination_path + "/sodoff.csproj") \
           ):
                ret = messagebox.showwarning("Warning!", "Selected directory DO NOT contain SoDOff server!", detail="Are you really sure you want to continue?", type='yesnocancel', default='cancel')
                if ret != 'yes':
                    destination_path = None
                    return
        destination_input.configure(text=destination_path)
    
    version_label = tk.Label(root, text="Please choose version", font=("Arial", 10, "italic"), **guisettings)
    version_label.grid(row=1, column=0, columnspan=1, sticky="n")
    
    version_dropdown = ttk.Combobox(root, textvariable=version, values=list(server_config["versions"].keys()), state="readonly", width=15)
    version_dropdown.grid(row=3, column=0, columnspan=1, pady=(5,10))
    
    destination_label = tk.Label(root, text="Please choose server folder", font=("Arial", 10, "italic"), **guisettings)
    destination_label.grid(row=1, column=1, columnspan=5, sticky="n")
    
    destination_input = tk.Button(root, height=1, width=60, command=select_server_directory, text="")
    destination_input.grid(row=3, column=1, columnspan=5, pady=(5,10))
    
    download_button = tk.Button(root, text="Download", command=lambda:download_assets(update=False), **guisettings)
    download_button.grid(row=5, column=0, pady=(5,10))
    
    update_button = tk.Button(root, text="Update", command=lambda:download_assets(update=True), **guisettings)
    update_button.grid(row=5, column=1, pady=(5,10))
    
    log_output = scrolledtext.ScrolledText(root, width=110, height=13)
    log_output.grid(row=4, column=0, columnspan=6, pady=(5,10), padx=15)
    
    update_button = tk.Button(root, text="Stop", command=stop_download_assets, **guisettings)
    update_button.grid(row=5, column=5, pady=(5,10))
    
    update_button = tk.Button(root, text="Force Stop", command=force_stop_download_assets, **guisettings)
    update_button.grid(row=5, column=4, pady=(5,10))
    
    root.mainloop()
    return 3
    


if __name__ == "__main__":
    freeze_support()
    
    import argparse
    parser = argparse.ArgumentParser(
        usage=f'''
   {sys.argv[0]} --help
   {sys.argv[0]} --config CONFIG --list-name LIST_NAME [--update]
   {sys.argv[0]} --url-prefix URL_PREFIX --path-list PATH_LIST [--update]
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config", action="store",
        help=f'json file or URL to json file with server configuration (default: {dafault_server_config})'
    )
    parser.add_argument(
        "--list-name", action="store",
        help='name of path list specified in config json'
    )

    parser.add_argument(
        "--url-prefix", action="store",
        help='urlprefix used for downloading files from path-list'
    )
    parser.add_argument(
        "--path-list", action="store",
        help='list of path to download (one file per line, md5sum format when -u is used)'
    )

    parser.add_argument(
        '-u', "--update", action="store_true",
        help='run in update mode (verify md5sum of file and replace files with a different checksum than the one given on the path-list)'
    )

    args, _ = parser.parse_known_args()

    if args.list_name is not None:
        if args.config is None:
            args.config = dafault_server_config
        server_config = getServerConfig(args.config)

        if not args.list_name in server_config["versions"] or not "src" in server_config["versions"][args.list_name]:
            raise BaseException("Invalid --list-name argument value")

        parallel = runDownloadFromConfig(server_config, args.list_name, args.update)
        if parallel:
            parallel.pool.close()
            parallel.pool.join()

    elif args.url_prefix is not None and args.path_list is not None :
        ret = downloadAssets(open(args.path_list), DownloadSettings(sleep_time=2, urlprefix=args.url_prefix, update_mode=args.update))
        print(ret[1])
        exit(ret[0])
    else:
        runGui(dafault_server_config)
