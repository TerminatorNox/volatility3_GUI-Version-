import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import threading
import sys
import os
import signal
import webbrowser
import platform
import ctypes
from datetime import datetime
import shutil
import re

# Attempting to import PIL for high-quality PNG/JPG handling
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# --- Enterprise Forensic Palette ---
BASE_BG = "#0D1117"        # Midnight Pearl
SIDEBAR_BG = "#010409"     # Deep Obsidian
NAV_ACTIVE = "#1F2937"     # Subtle Highlight
ACCENT_BLUE = "#58A6FF"    # Professional Cobalt
ACCENT_CYAN = "#39D353"    # Success Mint
ACCENT_PURPLE = "#BC8CFF"  # Logic Purple
WARN_GOLD = "#E3B341"      # Warning Amber
CRIT_RED = "#F85149"       # Critical Coral
TEXT_MAIN = "#C9D1D9"      # Primary Gray
TEXT_MUTED = "#8B949E"     # Metadata Gray
BORDER_COLOR = "#30363D"   # Subtle Separator

# --- Font Specifications ---
UI_HEADER = ("Segoe UI Semibold", 18)
UI_SUB = ("Segoe UI", 11, "bold")
UI_REG = ("Segoe UI", 10)
UI_MONO = ("Consolas", 10)

# --- Command Registry ---
LINUX_COMMANDS = [
    "linux.cpuinfo.CpuInfo", "linux.dmesg.Dmesg", "linux.iomem.IOMem", 
    "linux.slabinfo.SlabInfo", "linux.mounts.Mounts", "linux.pslist.PsList", 
    "linux.psaux.PsAux", "linux.pstree.PsTree", "linux.lsof.Lsof", 
    "linux.proc.Maps", "linux.bash.Bash", "linux.lsmod.LsMod", 
    "linux.check_afinfo.Check_afinfo", "linux.check_tty.Check_tty", 
    "linux.arp.Arp", "linux.ifconfig.Ifconfig", "linux.netstat.NetStat"
]

WINDOWS_COMMANDS = [
    "windows.info.Info", "windows.pslist.PsList", "windows.psscan.PsScan", 
    "windows.pstree.PsTree", "windows.psxview.PsXView", "windows.cmdline.CmdLine",
    "windows.netstat.NetStat", "windows.netscan.NetScan", "windows.filescan.FileScan",
    "windows.handles.Handles", "windows.dlllist.DllList", "windows.malfind.MalFind", 
    "windows.registry.hivelist.HiveList", "windows.registry.hivescan.HiveScan",
    "windows.registry.printkey.PrintKey", "windows.registry.userassist.UserAssist",
    "windows.getservicesids.GetServiceSIDs", "windows.getsids.GetSIDs",
    "windows.sessions.Sessions", "windows.driverscan.DriverScan",
    "windows.modules.Modules", "windows.modscan.ModScan", "windows.callbacks.Callbacks",
    "windows.idt.IDT", "windows.gdt.GDT", "windows.ssdt.SSDT",
    "windows.vaddump.VadDump", "windows.vadinfo.VadInfo", "windows.virtmap.VirtMap",
    "windows.mftscan.MFTScan", "windows.memmap.Memmap", "windows.ldrmodules.LdrModules",
    "windows.poolscanner.PoolScanner", "windows.privs.Privs", "windows.symlinkscan.SymlinkScan",
    "windows.verinfo.VerInfo", "windows.devicetree.DeviceTree", "windows.envars.Envars",
    "windows.joblinks.JobLinks", "windows.strings.Strings", "windows.moddump.ModDump",
    "windows.procdump.ProcDump", "windows.driversync.DriverSync", "windows.crashdump.CrashDump",
    "windows.svcscan.SvcScan", "windows.bigpools.BigPools", "windows.mutantscan.MutantScan"
]

# --- System Logic ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0 if platform.system() == 'Windows' else os.getuid() == 0
    except: return False

def elevate_privileges():
    try:
        if platform.system() == 'Windows':
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        else:
            os.execv('/usr/bin/sudo', ['sudo', sys.executable] + sys.argv)
    except: sys.exit()

class VortexAnalyst(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Terminator | Advanced Memory Forensics")
        self.geometry("1300x900")
        self.configure(bg=BASE_BG)
        self.withdraw() # Hide the main window initially for the splash screen
        
        # State Management
        self.selected_os = None
        self.file_path = tk.StringVar()
        self.is_running = False
        self.current_process = None
        self.verbose_val = tk.IntVar(value=1) # Default to detailed view
        self.search_val = tk.StringVar()
        self.auto_scroll = tk.BooleanVar(value=True)

        self.apply_styles()
        
        # Show Splash Screen before initializing UI
        self.show_splash_screen()

    def show_splash_screen(self):
        """Creates a professional 5-second centered transparent splash screen."""
        self.splash = tk.Toplevel()
        self.splash.overrideredirect(True) # Remove borders/title bar
        self.splash.attributes("-topmost", True)
        
        # Windows-specific transparency: 'black' pixels will be invisible
        if platform.system() == "Windows":
            self.splash.attributes("-transparentcolor", "black")
        
        self.splash.configure(bg="black")

        img_path = "Image.png"
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Logic to handle Image if Pillow is installed and image exists
        if HAS_PIL and os.path.exists(img_path):
            try:
                full_img = Image.open(img_path)
                
                # Scale image to 40% of screen width while maintaining aspect ratio
                target_w = int(screen_w * 0.4)
                w_percent = (target_w / float(full_img.size[0]))
                target_h = int((float(full_img.size[1]) * float(w_percent)))
                
                img_scaled = full_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                self.splash_img = ImageTk.PhotoImage(img_scaled)
                
                # We use black as the background so it becomes transparent on Windows
                lbl = tk.Label(self.splash, image=self.splash_img, bg="black", borderwidth=0)
                lbl.pack()

                x = (screen_w // 2) - (target_w // 2)
                y = (screen_h // 2) - (target_h // 2)
                self.splash.geometry(f"{target_w}x{target_h}+{x}+{y}")
            except Exception:
                self.show_fallback_splash(screen_w, screen_h)
        else:
            self.show_fallback_splash(screen_w, screen_h)

        # Set 5-second timer
        self.after(5000, self.finalize_startup)

    def show_fallback_splash(self, screen_w, screen_h):
        """Fallback splash screen if image or PIL is missing."""
        fallback_w, fallback_h = 500, 300
        # If no image, we don't use the transparent attribute to ensure text is visible
        if platform.system() == "Windows":
            self.splash.attributes("-transparentcolor", "")
            
        tk.Label(self.splash, text="Terminator\nINITIALIZING CORE...", 
                 fg=ACCENT_BLUE, bg=BASE_BG, font=("Segoe UI", 24, "bold"), padx=50, pady=50).pack(expand=True, fill="both")
        
        x = (screen_w // 2) - (fallback_w // 2)
        y = (screen_h // 2) - (fallback_h // 2)
        self.splash.geometry(f"{fallback_w}x{fallback_h}+{x}+{y}")

    def finalize_startup(self):
        """Destroys splash and launches main dashboard."""
        if hasattr(self, 'splash'):
            self.splash.destroy()
        self.deiconify() # Show main window
        self.init_ui()
        self.route_dashboard()
        self.start_clock_daemon()

    def apply_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        
        s.configure("TCombobox", 
                    fieldbackground="#2D333B", 
                    background=SIDEBAR_BG, 
                    foreground=TEXT_MAIN, 
                    bordercolor=BORDER_COLOR, 
                    arrowcolor=ACCENT_BLUE, 
                    font=UI_REG)
        
        s.map("TCombobox", 
              fieldbackground=[("readonly", "#2D333B"), ("focus", "#30363D")],
              foreground=[("readonly", TEXT_MAIN)])

        self.option_add("*TCombobox*Listbox.background", SIDEBAR_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_MAIN)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_BLUE)
        self.option_add("*TCombobox*Listbox.selectForeground", SIDEBAR_BG)
        self.option_add("*TCombobox*Listbox.font", UI_REG)

        s.configure("Vortex.Horizontal.TProgressbar", troughcolor=SIDEBAR_BG, bordercolor=BORDER_COLOR, background=ACCENT_BLUE)

    def init_ui(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=SIDEBAR_BG, pady=40)
        brand.pack(fill="x")
        tk.Label(brand, text="Terminator", font=("Segoe UI", 26, "bold"), bg=SIDEBAR_BG, fg=ACCENT_BLUE).pack()
        tk.Label(brand, text="EDR & FORENSICS SUITE", font=("Segoe UI", 8, "bold"), bg=SIDEBAR_BG, fg=TEXT_MUTED, pady=5).pack()

        self.menu_items = [
            ("🏠  Home ", self.route_dashboard, TEXT_MAIN),
            
        ]

        self.nav_btns = {}
        for text, cmd, color in self.menu_items:
            f = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
            f.pack(fill="x", padx=10, pady=2)
            btn = tk.Button(f, text=text, command=cmd, bg=SIDEBAR_BG, fg=color, 
                            font=UI_SUB, relief="flat", padx=20, pady=12, anchor="w",
                            activebackground=NAV_ACTIVE, activeforeground=color, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=NAV_ACTIVE))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=SIDEBAR_BG))
            self.nav_btns[text] = btn

        footer = tk.Frame(self.sidebar, bg=SIDEBAR_BG, pady=20)
        footer.pack(side="bottom", fill="x")
        tk.Button(footer, text="Purge Symbol Cache", command=self.action_purge_symbols, bg=SIDEBAR_BG, 
                  fg=TEXT_MUTED, relief="flat", font=("Segoe UI", 8)).pack(fill="x")
        self.clock_lbl = tk.Label(footer, text="", font=UI_MONO, bg=SIDEBAR_BG, fg=TEXT_MUTED)
        self.clock_lbl.pack(pady=10)

        self.content = tk.Frame(self, bg=BASE_BG)
        self.content.pack(side="right", fill="both", expand=True)

    def reset_content(self):
        for w in self.content.winfo_children(): w.destroy()

    def start_clock_daemon(self):
        def update():
            if self.clock_lbl.winfo_exists():
                self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S  |  %Y-%m-%d"))
                self.after(1000, update)
        update()

    def route_dashboard(self):
        self.reset_content()
        h = tk.Frame(self.content, bg=BASE_BG, padx=50, pady=50)
        h.pack(fill="x")
        tk.Label(h, text="Operational Overview", font=UI_HEADER, bg=BASE_BG, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(h, text="Welcome to Vortex Analyst. Select a module from the sidebar to start your investigation.", font=UI_REG, bg=BASE_BG, fg=TEXT_MUTED).pack(anchor="w", pady=5)

        sc = ACCENT_CYAN if is_admin() else CRIT_RED
        st = "SYSTEM PRIVILEGES: ELEVATED (ROOT/ADMIN)" if is_admin() else "SYSTEM PRIVILEGES: RESTRICTED (USER)"
        card = tk.Frame(self.content, bg=SIDEBAR_BG, padx=20, pady=15, highlightbackground=sc, highlightthickness=1)
        card.pack(fill="x", padx=50, pady=10)
        tk.Label(card, text=st, font=UI_SUB, bg=SIDEBAR_BG, fg=sc).pack(side="left")

        grid = tk.Frame(self.content, bg=BASE_BG, padx=50, pady=20)
        grid.pack(fill="both", expand=True)

        actions = [
            ("Windows Analysis", "Investigate NT kernel memory artifacts.", ACCENT_BLUE, lambda: self.route_analyst("windows")),
            ("Linux Analysis", "Deep dive into ELF/Kernel structures.", ACCENT_PURPLE, lambda: self.route_analyst("linux")),
            ("LiME Installer", "Deploy memory extractor on Linux hosts.", ACCENT_CYAN, self.route_lime),
            ("Belkasoft Capture", "Live RAM capture tool for Windows systems.", "#FFD700", lambda: webbrowser.open("https://www.softpedia.com/get/Tweak/Memory-Tweak/Belkasoft-Live-RAM-Capturer.shtml")),
            ("Full Suite Deploy", "Initialize Volatility 3 and all core modules.", ACCENT_BLUE, self.route_autodeploy),
            ("Repair Utility", "Fix broken Python dependencies and caches.", WARN_GOLD, self.route_repair),
        ]

        for i, (t, d, c, cmd) in enumerate(actions):
            f = tk.Frame(grid, bg=SIDEBAR_BG, width=280, height=150, padx=20, pady=20)
            f.grid(row=i//3, column=i%3, padx=10, pady=10)
            f.pack_propagate(False)
            tk.Label(f, text=t, font=UI_SUB, bg=SIDEBAR_BG, fg=c).pack(anchor="w")
            tk.Label(f, text=d, font=("Segoe UI", 9), bg=SIDEBAR_BG, fg=TEXT_MUTED, wraplength=240, justify="left").pack(anchor="w", pady=10)
            b = tk.Button(f, text="Launch Module", command=cmd, bg=NAV_ACTIVE, fg=c, font=UI_SUB, relief="flat", pady=5)
            b.pack(side="bottom", fill="x")

    def route_analyst(self, os_type):
        self.selected_os = os_type
        self.reset_content()
        
        header = tk.Frame(self.content, bg=BASE_BG, padx=30, pady=30)
        header.pack(fill="x")
        tk.Label(header, text=f"ANALYST NODE: {os_type.upper()}", font=UI_HEADER, bg=BASE_BG, fg=ACCENT_BLUE).pack(side="left")

        cp = tk.Frame(self.content, bg=SIDEBAR_BG, padx=25, pady=25)
        cp.pack(fill="x", padx=30, pady=5)

        r1 = tk.Frame(cp, bg=SIDEBAR_BG)
        r1.pack(fill="x", pady=5)
        tk.Label(r1, text="MEMORY IMAGE", font=UI_SUB, bg=SIDEBAR_BG, fg=TEXT_MUTED, width=15, anchor="w").pack(side="left")
        tk.Entry(r1, textvariable=self.file_path, bg=NAV_ACTIVE, fg=TEXT_MAIN, font=UI_MONO, relief="flat", insertbackground=TEXT_MAIN).pack(side="left", fill="x", expand=True, padx=10, ipady=4)
        tk.Button(r1, text="MOUNT", command=self.action_browse, bg=ACCENT_BLUE, fg=SIDEBAR_BG, relief="flat", font=UI_SUB, padx=20).pack(side="right")

        r2 = tk.Frame(cp, bg=SIDEBAR_BG)
        r2.pack(fill="x", pady=5)
        tk.Label(r2, text="CORE PLUGIN", font=UI_SUB, bg=ACCENT_CYAN, fg=SIDEBAR_BG, width=15, anchor="w", padx=5).pack(side="left")
        cmds = WINDOWS_COMMANDS if os_type == "windows" else LINUX_COMMANDS
        self.cb_plugin = ttk.Combobox(r2, values=cmds, state="readonly", style="TCombobox")
        self.cb_plugin.pack(side="left", fill="x", expand=True, padx=10)
        self.cb_plugin.set(cmds[0])
        
        self.btn_start = tk.Button(r2, text="RUN ANALYSIS", command=self.action_start, bg=ACCENT_CYAN, fg=SIDEBAR_BG, relief="flat", font=UI_SUB, width=15)
        self.btn_start.pack(side="right", padx=(5, 0))
        self.btn_stop = tk.Button(r2, text="STOP", command=self.action_stop, bg=CRIT_RED, fg=TEXT_MAIN, relief="flat", font=UI_SUB, state="disabled", width=10)
        self.btn_stop.pack(side="right")

        r3 = tk.Frame(cp, bg=SIDEBAR_BG)
        r3.pack(fill="x", pady=(15, 0))
        tk.Label(r3, text="VERBOSITY:", font=UI_REG, bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(side="left")
        v = tk.OptionMenu(r3, self.verbose_val, 0, 1, 2, 3)
        v.config(bg=NAV_ACTIVE, fg=TEXT_MAIN, relief="flat", highlightthickness=0, font=UI_REG)
        v.pack(side="left", padx=5)

        tk.Label(r3, text="SEARCH:", font=UI_REG, bg=SIDEBAR_BG, fg=TEXT_MUTED, padx=10).pack(side="left")
        tk.Entry(r3, textvariable=self.search_val, bg=NAV_ACTIVE, fg=ACCENT_BLUE, font=UI_MONO, relief="flat", width=25).pack(side="left", padx=5)
        tk.Button(r3, text="FIND", command=self.action_search, bg=NAV_ACTIVE, fg=TEXT_MAIN, relief="flat", font=UI_REG).pack(side="left")
        tk.Button(r3, text="CLEAR", command=lambda: self.txt_out.delete(1.0, tk.END), bg=SIDEBAR_BG, fg=ACCENT_PURPLE, relief="flat", font=UI_REG).pack(side="right", padx=10)
        tk.Checkbutton(r3, text="SCROLL", variable=self.auto_scroll, bg=SIDEBAR_BG, fg=TEXT_MUTED, selectcolor=NAV_ACTIVE, activebackground=SIDEBAR_BG, font=UI_REG).pack(side="right")

        self.pb = ttk.Progressbar(self.content, orient="horizontal", mode="indeterminate", style="Vortex.Horizontal.TProgressbar")
        self.pb.pack(fill="x", padx=30, pady=(10, 0))
        self.lbl_hud = tk.Label(self.content, text="STATUS: STANDBY", bg=BASE_BG, fg=ACCENT_BLUE, font=UI_MONO, height=1)
        self.lbl_hud.pack(fill="x", padx=30)

        out_f = tk.Frame(self.content, bg=SIDEBAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        out_f.pack(fill="both", expand=True, padx=30, pady=10)
        self.txt_out = tk.Text(out_f, bg=SIDEBAR_BG, fg=TEXT_MAIN, font=UI_MONO, relief="flat", padx=15, pady=15, wrap="none", insertbackground=TEXT_MAIN)
        ys = tk.Scrollbar(out_f, command=self.txt_out.yview)
        xs = tk.Scrollbar(out_f, orient="horizontal", command=self.txt_out.xview)
        self.txt_out.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        self.txt_out.pack(fill="both", expand=True)

    def route_lime(self):
        self.reset_content()
        tk.Label(self.content, text="LiME DEPLOYMENT ENGINE", font=UI_HEADER, bg=BASE_BG, fg=ACCENT_CYAN, padx=40, pady=30).pack(anchor="w")
        btn_f = tk.Frame(self.content, bg=BASE_BG, padx=40)
        btn_f.pack(fill="x")
        cmds = [
            ("UPDATE APT", "sudo apt update"),
            ("HEADERS", "sudo apt install -y git build-essential linux-headers-$(uname -r)"),
            ("FETCH SOURCE", "sudo git clone https://github.com/504ensicsLabs/LiME.git"),
            ("BUILD", "cd LiME/src && make"),
            ("CAPTURE", "cd LiME/src && sudo insmod lime-$(uname -r).ko path=/tmp/ram_dump.lime format=lime")
        ]
        for t, c in cmds:
            tk.Button(btn_f, text=t, command=lambda cmd=c: self.action_run_installer(cmd),
                      bg=SIDEBAR_BG, fg=ACCENT_CYAN, relief="flat", font=UI_SUB, padx=15, pady=10).pack(side="left", padx=5)
        self.txt_out = tk.Text(self.content, bg=SIDEBAR_BG, fg=ACCENT_CYAN, font=UI_MONO, relief="flat", padx=20, pady=20)
        self.txt_out.pack(fill="both", expand=True, padx=40, pady=20)

    def route_repair(self):
        self.reset_content()
        tk.Label(self.content, text="ENVIRONMENT REPAIR UTILITY", font=UI_HEADER, bg=BASE_BG, fg=WARN_GOLD, padx=40, pady=30).pack(anchor="w")
        self.txt_out = tk.Text(self.content, bg=SIDEBAR_BG, fg=TEXT_MAIN, font=UI_MONO, relief="flat", padx=20, pady=20)
        self.txt_out.pack(fill="both", expand=True, padx=40, pady=20)
        threading.Thread(target=self.logic_repair, daemon=True).start()

    def route_autodeploy(self):
        self.reset_content()
        tk.Label(self.content, text=f"VOLATILITY 3 AUTO-DEPLOY ({platform.system()})", font=UI_HEADER, bg=BASE_BG, fg=ACCENT_BLUE, padx=40, pady=30).pack(anchor="w")
        self.txt_out = tk.Text(self.content, bg=SIDEBAR_BG, fg=TEXT_MAIN, font=UI_MONO, relief="flat", padx=20, pady=20)
        self.txt_out.pack(fill="both", expand=True, padx=40, pady=20)
        threading.Thread(target=self.logic_autodeploy, args=(platform.system(),), daemon=True).start()

    def action_browse(self):
        f = filedialog.askopenfilename(title="Select Forensic Image", filetypes=[("Forensic Images", "*.mem *.lime *.raw *.bin *.vmem"), ("All", "*.*")])
        if f: self.file_path.set(f)

    def action_search(self):
        q = self.search_val.get()
        self.txt_out.tag_remove('match', '1.0', tk.END)
        if q:
            idx = '1.0'
            while 1:
                idx = self.txt_out.search(q, idx, nocase=1, stopindex=tk.END)
                if not idx: break
                last = f"{idx}+{len(q)}c"
                self.txt_out.tag_add('match', idx, last)
                idx = last
            self.txt_out.tag_config('match', background=ACCENT_BLUE, foreground=SIDEBAR_BG)

    def action_start(self):
        if self.is_running or not self.file_path.get(): return
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.pb.start(10)
        self.txt_out.delete(1.0, tk.END)
        self.log_to_term("--- ANALYSIS SESSION INITIATED ---")
        threading.Thread(target=self.logic_volatility, args=(self.file_path.get(), self.cb_plugin.get()), daemon=True).start()

    def action_stop(self):
        if self.current_process:
            try:
                if platform.system() == "Windows": subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)])
                else: os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
            except: pass
            self.log_to_term("--- SESSION TERMINATED BY USER ---", True)

    def action_purge_symbols(self):
        path = os.path.join(os.getcwd(), "volatility3", "volatility3", "symbols")
        if not os.path.exists(path):
            path = os.path.expanduser("~/.cache/volatility3/symbols") if platform.system() != "Windows" else os.path.join(os.environ.get('LOCALAPPDATA', ''), 'volatility3', 'symbols')
        if messagebox.askyesno("Confirm Purge", f"Delete cached symbols?\n{path}"):
            try:
                if os.path.exists(path): shutil.rmtree(path); messagebox.showinfo("Success", "Cache Purged.")
                else: messagebox.showwarning("Error", "Cache path not found.")
            except Exception as e: messagebox.showerror("Error", str(e))

    def action_run_installer(self, cmd):
        self.log_to_term(f"EXECUTING: {cmd}")
        threading.Thread(target=self.logic_shell, args=(cmd,), daemon=True).start()

    def logic_shell(self, cmd):
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout: self.log_to_term(f"  {line.strip()}")
            p.wait()
        except Exception as e: self.log_to_term(f"FATAL: {str(e)}", True)

    def logic_repair(self):
        self.log_to_term("[!] Verifying forensic environment...")
        py = f'"{sys.executable}"'
        cmds = [f"{py} -m pip install --upgrade pip", f"{py} -m pip install --user pefile pycryptodome yara-python yara-x capstone jsonschema", f"{py} -m pip install --user -r volatility3/requirements.txt"]
        for c in cmds: self.logic_shell(c)
        self.log_to_term("[+] Repair complete. Restarting in 3s...")
        self.after(3000, lambda: os.execl(sys.executable, sys.executable, *sys.argv))

    def logic_autodeploy(self, os_name):
        py = f'"{sys.executable}"'
        cmds = [f"{py} -m pip install --upgrade pip", "git clone https://github.com/volatilityfoundation/volatility3.git", f"{py} -m pip install --user pefile pycryptodome yara-python capstone", f"{py} -m pip install --user -r volatility3\\requirements.txt" if os_name=="Windows" else "pip3 install --user -r volatility3/requirements.txt"]
        if os_name != "Windows": cmds.insert(0, "sudo apt update && sudo apt install -y python3-pip git python3-setuptools python3-dev")
        for c in cmds: self.logic_shell(c)
        if os_name == "Windows": # Double check for Windows path style
             if os.path.exists("volatility3"): self.after(3000, lambda: os.execl(sys.executable, sys.executable, *sys.argv))
        else:
             if os.path.exists("volatility3"): self.after(3000, lambda: os.execl(sys.executable, sys.executable, *sys.argv))

    def logic_volatility(self, img, plugin):
        try:
            v_py = os.path.join(os.getcwd(), "volatility3", "vol.py")
            exec_path = v_py if os.path.exists(v_py) else "vol"
            cmd = [sys.executable, "-u", exec_path, "-f", img]
            if self.verbose_val.get() > 0: cmd.append("-" + "v" * self.verbose_val.get())
            cmd.append(plugin)
            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, shell=(platform.system()=="Windows"), bufsize=1, universal_newlines=True
            )
            results_found = False
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.is_running: break
                clean = line.strip()
                if not clean: continue
                if any(x in clean for x in ["Progress:", "Scanning", "Stacking"]):
                    self.lbl_hud.after(0, lambda l=clean: self.lbl_hud.config(text=f"KERNEL: {l}", fg=ACCENT_PURPLE))
                    if self.verbose_val.get() >= 2: self.log_to_term(clean)
                    continue
                if any(x in clean for x in ["Offset", "PID", "PPID", "Name", "---"]):
                    results_found = True
                    self.lbl_hud.after(0, lambda: self.lbl_hud.config(text="STATUS: DATA STREAM ACTIVE", fg=ACCENT_CYAN))
                self.log_to_term(clean)
            self.current_process.stdout.close()
            rc = self.current_process.wait()
            self.lbl_hud.after(0, lambda: self.lbl_hud.config(text=f"SESSION COMPLETED: {rc}", fg=ACCENT_BLUE))
        except Exception as e:
            self.log_to_term(f"CRITICAL FAULT: {str(e)}", True)
        finally:
            self.is_running = False
            self.pb.after(0, self.pb.stop)
            self.btn_start.after(0, lambda: self.btn_start.config(state="normal"))
            self.btn_stop.after(0, lambda: self.btn_stop.config(state="disabled"))

    def log_to_term(self, msg, err=False):
        if not self.winfo_exists(): return
        def update():
            ts = datetime.now().strftime("[%H:%M:%S] ")
            if err or "ERROR" in msg or "Exception" in msg or "CRITICAL" in msg: tag = "err"
            elif any(x in msg for x in ["Offset", "PID", "Name", "Property", "Value", "---"]): tag = "head"
            elif any(x in msg for x in ["Symbols", "Volatility", "Framework", "pdb"]): tag = "info"
            else: tag = "norm"
            self.txt_out.tag_config("err", foreground=CRIT_RED)
            self.txt_out.tag_config("head", foreground=ACCENT_BLUE, font=UI_SUB)
            self.txt_out.tag_config("info", foreground=ACCENT_CYAN)
            self.txt_out.tag_config("norm", foreground=TEXT_MAIN)
            self.txt_out.insert(tk.END, ts + msg + "\n", tag)
            if self.auto_scroll.get(): self.txt_out.see(tk.END)
        self.txt_out.after(0, update)

if __name__ == "__main__":
    if not is_admin(): elevate_privileges()
    else: VortexAnalyst().mainloop()