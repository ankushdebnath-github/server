# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'LpuNest_Cur.py'
# Bytecode version: 3.10.b1 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global paused
import os
import sys
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import subprocess
import hashlib
import uuid
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QMetaObject, Q_ARG
import keyboard
import ctypes
from ctypes import wintypes, byref, POINTER, c_long
import pythoncom
import win32gui
import win32con
import win32api
import win32clipboard
import winreg
import time
from pywinauto import Application
import comtypes
import comtypes.client
import logging
_log_path = os.path.join(os.path.expanduser('~'), 'pea_bot_log.txt')
logging.basicConfig(filename=_log_path, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
_log = logging.getLogger('PeaBot')
_original_print = print
def print(*args, **kwargs):
    msg = ' '.join((str(a) for a in args))
    _original_print(msg, **kwargs)
    try:
        _log.info(msg)
    except:
        return None
print(f'=== Pea Bot Started === Log: {_log_path}')
# Authentication removed - app runs without authorization
GENERATE_URL = "https://lpu-helper-backend.onrender.com/generate"  # Change to your Render URL when deployed
AUTH_SERVER_URL = None

# API Configuration
API_TOKEN_LPU = "lpu-super-secret-token-2024"
APP_ID_LPU = "lpu-helper"
session = requests.Session()
_retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=['POST'])
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=10, pool_maxsize=10)
session.mount('https://', _adapter)
session.mount('http://', _adapter)
HWID_CACHE_FILE = os.path.expanduser('~/.hwid_cache')
paused = False
def get_hwid():
    # irreducible cflow, using cdg fallback
    # ***<module>.get_hwid: Failure: Compilation Error
    try:
        cpu_id = 'unknown-cpu'
        try:
            output = subprocess.check_output('wmic cpu get ProcessorId', shell=True)
            cpu_id = output.decode().split('\n')[1].strip()
        except:
            pass
        bios_uuid = 'unknown-bios'
        try:
            output = subprocess.check_output('wmic csproduct get UUID', shell=True)
            bios_uuid = output.decode().split('\n')[1].strip()
        except:
            pass
        machine_guid = 'unknown-guid'
        try:
            output = subprocess.check_output('reg query HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid', shell=True)
            machine_guid = output.decode().split()[(-1)].strip()
        except:
            pass
        baseboard_serial = 'unknown-baseboard'
        try:
            output = subprocess.check_output('wmic baseboard get serialnumber', shell=True)
            baseboard_serial = output.decode().split('\n')[1].strip()
        except:
            pass
        raw_hwid = f'{cpu_id}|{bios_uuid}|{machine_guid}|{baseboard_serial}'
        hwid_hash = hashlib.sha256(raw_hwid.encode()).hexdigest()
        return hwid_hash
    except Exception as e:
        mac = str(uuid.getnode())
        return hashlib.sha256(mac.encode()).hexdigest()
            return 'error-generating-hwid'
def get_stable_hwid():
    # irreducible cflow, using cdg fallback
    # ***<module>.get_stable_hwid: Failure: Different control flow
    if os.path.exists(HWID_CACHE_FILE):
        with open(HWID_CACHE_FILE, 'r') as f:
            cached_hwid = f.read().strip()
            if cached_hwid and cached_hwid!= 'error-generating-hwid':
                return cached_hwid
            pass
            hwid = get_hwid()
            try:
                with open(HWID_CACHE_FILE, 'w') as f:
                    f.write(hwid)
            except:
                pass
                return hwid
            return hwid
    return hwid
def toggle_pause():
    global paused
    paused = not paused
    print(f'Paused: {paused}')
def check_pause():
    return None
def send_keys(hwnd, text):
    for char in text:
        while paused:
            time.sleep(0.1)
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        if char == ' ':
            time.sleep(0.04)
        else:
            if char == '\t':
                time.sleep(0.05)
            else:
                time.sleep(0.01)
def auto_typer(text):
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    else:
        clean_text = text
        if '```' in clean_text:
            parts = clean_text.split('```')
            if len(parts) >= 2:
                clean_text = parts[1]
                if clean_text.startswith('python'):
                    clean_text = clean_text[6:]
                else:
                    if clean_text.startswith('sql'):
                        clean_text = clean_text[3:]
                    else:
                        if clean_text.startswith('html'):
                            clean_text = clean_text[4:]
        clean_text = clean_text.rstrip()
        if not clean_text:
            return None
        else:
            lines = clean_text.split('\n')
            for line in lines:
                while paused:
                    time.sleep(0.1)
                line_to_type = line.rstrip()
                if line_to_type:
                    send_keys(hwnd, line_to_type)
                time.sleep(0.05)
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                time.sleep(0.02)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
                time.sleep(0.05)
def find_chrome_renderer(hwnd):
    # ***<module>.find_chrome_renderer: Failure: Different bytecode
    renderer = [None]
    def callback(child_hwnd, _):
        try:
            cls = win32gui.GetClassName(child_hwnd)
            if 'RenderWidgetHostHWND' in cls:
                renderer[0] = child_hwnd
                return False
            else:
                return True
        except:
            return True
    try:
        win32gui.EnumChildWindows(hwnd, callback, None)
    except:
        return renderer[0]
    return renderer[0]
def auto_clipboard_capture():
    """Auto select all + copy text from the focused window.\n    First clicks in the content area to set focus, then Ctrl+A + Ctrl+C."""
    print('🔄 Phase 0: Auto clipboard capture (Click + Ctrl+A + Ctrl+C)...')
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        print('  ⚠ No foreground window')
        return None
    else:
        title = ''
        try:
            title = win32gui.GetWindowText(hwnd)
        except:
            pass
        print(f'  Target window: \'{title}\' (hwnd={hwnd})')
        INPUT_KEYBOARD = 1
        INPUT_MOUSE = 0
        KEYEVENTF_KEYUP = 2
        MOUSEEVENTF_LEFTDOWN = 2
        MOUSEEVENTF_LEFTUP = 4
        MOUSEEVENTF_ABSOLUTE = 32768
        MOUSEEVENTF_MOVE = 1
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [('dx', ctypes.c_long), ('dy', ctypes.c_long), ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))]
        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [('uMsg', wintypes.DWORD), ('wParamL', wintypes.WORD), ('wParamH', wintypes.WORD)]
        class INPUT_UNION(ctypes.Union):
            _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('hi', HARDWAREINPUT)]
        class INPUT(ctypes.Structure):
            _fields_ = [('type', wintypes.DWORD), ('union', INPUT_UNION)]
        def send_key_input(*key_actions):
            n = len(key_actions)
            inputs = (INPUT * n)()
            for i, (vk, is_up) in enumerate(key_actions):
                inputs[i].type = INPUT_KEYBOARD
                inputs[i].union.ki.wVk = vk
                inputs[i].union.ki.dwFlags = KEYEVENTF_KEYUP if is_up else 0
            ctypes.windll.user32.SendInput(n, inputs, ctypes.sizeof(INPUT))
        def click_at(screen_x, screen_y):
            """Click at absolute screen coordinates using SendInput."""
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            abs_x = int(screen_x * 65535 / sw)
            abs_y = int(screen_y * 65535 / sh)
            inputs = (INPUT * 3)()
            inputs[0].type = INPUT_MOUSE
            inputs[0].union.mi.dx = abs_x
            inputs[0].union.mi.dy = abs_y
            inputs[0].union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
            inputs[1].type = INPUT_MOUSE
            inputs[1].union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
            inputs[2].type = INPUT_MOUSE
            inputs[2].union.mi.dwFlags = MOUSEEVENTF_LEFTUP
            ctypes.windll.user32.SendInput(3, inputs, ctypes.sizeof(INPUT))
        VK_CONTROL = 17
        VK_A = 65
        VK_C = 67
        VK_MENU = 18
        VK_ESCAPE = 27
        send_key_input((VK_MENU, True), (VK_CONTROL, True))
        time.sleep(0.2)
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            click_x = left + int((right - left) * 0.6)
            click_y = top + int((bottom - top) * 0.5)
            print(f'  → Clicking at ({click_x}, {click_y}) to focus content area...')
            click_at(click_x, click_y)
            time.sleep(0.3)
        except Exception as e:
            print(f'  ⚠ Click failed: {e}')
        old_clipboard = None
        try:
            win32clipboard.OpenClipboard()
            try:
                old_clipboard = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except:
                pass
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        except:
            pass
        print('  → Sending Ctrl+A...')
        send_key_input((VK_CONTROL, False), (VK_A, False), (VK_A, True), (VK_CONTROL, True))
        time.sleep(0.5)
        print('  → Sending Ctrl+C...')
        send_key_input((VK_CONTROL, False), (VK_C, False), (VK_C, True), (VK_CONTROL, True))
        time.sleep(0.6)
        send_key_input((VK_ESCAPE, False), (VK_ESCAPE, True))
        text = None
        try:
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except:
            pass
        if text and len(text.strip()) > 30 and (text!= old_clipboard):
            print(f'  ✓ SendInput clipboard got {len(text)} chars!')
            print(f'  First 200 chars: {text[:200]}')
            return text.strip()
        else:
            if text:
                print(f'  ⚠ Got clipboard but too short ({len(text)} chars): {text[:100]}')
            else:
                print('  ⚠ Clipboard was empty after Ctrl+A/C')
            print('  → Trying PostMessage to Chrome renderer...')
            renderer = find_chrome_renderer(hwnd)
            target = renderer if renderer else hwnd
            print(f"  → PostMessage target: {('Renderer' if renderer else 'Main')} (hwnd={target})")
            try:
                try:
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.CloseClipboard()
                except:
                    pass
                WM_KEYDOWN = 256
                WM_KEYUP = 257
                win32api.PostMessage(target, WM_KEYDOWN, VK_CONTROL, 0)
                win32api.PostMessage(target, WM_KEYDOWN, VK_A, 0)
                win32api.PostMessage(target, WM_KEYUP, VK_A, 0)
                win32api.PostMessage(target, WM_KEYUP, VK_CONTROL, 0)
                time.sleep(0.5)
                win32api.PostMessage(target, WM_KEYDOWN, VK_CONTROL, 0)
                win32api.PostMessage(target, WM_KEYDOWN, VK_C, 0)
                win32api.PostMessage(target, WM_KEYUP, VK_C, 0)
                win32api.PostMessage(target, WM_KEYUP, VK_CONTROL, 0)
                time.sleep(0.6)
                text2 = None
                try:
                    win32clipboard.OpenClipboard()
                    text2 = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if text2 and len(text2.strip()) > 30:
                    print(f'  ✓ PostMessage clipboard got {len(text2)} chars!')
                    return text2.strip()
            except Exception as e:
                print(f'  ⚠ PostMessage method failed: {e}')
            print('  ⚠ Auto clipboard: all methods failed')
            return None
def set_chrome_accessibility_registry():
    """Set Chrome/Chromium registry keys to force accessibility mode."""
    paths = ['Software\\Google\\Chrome\\Accessibility', 'Software\\Chromium\\Accessibility', 'Software\\Google\\Chrome', 'Software\\Chromium']
    for path in paths:
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, 'ManuallyEnabled', 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            print(f'  ✓ Registry set: HKCU\\{path}\\ManuallyEnabled=1')
        except:
            pass
def force_chrome_accessibility_on():
    # irreducible cflow, using cdg fallback
    """Force Chrome to enable its accessibility tree.\n    Chrome only builds its a11y tree when it detects a screen reader.\n    We tell Windows a screen reader is active -> Chrome responds."""
    # ***<module>.force_chrome_accessibility_on: Failure: Compilation Error
    SPI_SETSCREENREADER = 71
    SPIF_SENDCHANGE = 2
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETSCREENREADER, 1, None, SPIF_SENDCHANGE)
    print('✓ Screen reader flag ENABLED (Chrome will build accessibility tree)')
    EVENT_SYSTEM_ALERT = 2
        ctypes.windll.user32.NotifyWinEvent(EVENT_SYSTEM_ALERT, 0, 0, 0)
        return True
            return True
                except Exception as e:
                    print(f'⚠️ Could not set screen reader flag: {e}')
                    return False
def force_chrome_accessibility_off():
    """Reset screen reader flag after extraction"""
    try:
        SPI_SETSCREENREADER = 71
        SPIF_SENDCHANGE = 2
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETSCREENREADER, 0, None, SPIF_SENDCHANGE)
    except:
        return None
def _ensure_accessibility_typelib():
    """Load oleacc.dll type library so comtypes.gen.Accessibility exists"""
    # ***<module>._ensure_accessibility_typelib: Failure detected at line number 311 and instruction offset 16: Different bytecode
    try:
        from comtypes.gen import Accessibility
        return
    except ImportError:
        try:
            comtypes.client.GetModule('oleacc.dll')
            return True
        except Exception as e:
            print(f'  ⚠️ Could not load oleacc typelib: {e}')
            return False
    return True
def get_iaccessible_from_hwnd(hwnd):
    """Get IAccessible COM interface from a window handle using oleacc.dll"""
    try:
        if not _ensure_accessibility_typelib():
            return
        else:
            from comtypes.gen.Accessibility import IAccessible
            oleacc = ctypes.oledll.oleacc
            obj = POINTER(comtypes.IUnknown)()
            IID_IAccessible = comtypes.GUID('{618736e0-3c3d-11cf-810c-00aa00389b71}')
            OBJID_CLIENT = 4294967292
            result = oleacc.AccessibleObjectFromWindow(hwnd, OBJID_CLIENT, byref(IID_IAccessible), byref(obj))
            if result == 0 and obj:
                    acc = obj.QueryInterface(IAccessible)
                    return acc
    except Exception as e:
        print(f'  ⚠️ get_iaccessible error: {e}')
        return None
def traverse_iaccessible(acc, all_texts, seen, depth=0, max_depth=40):
    # irreducible cflow, using cdg fallback
    """Recursively traverse IAccessible tree and collect ALL text"""
    # ***<module>.traverse_iaccessible: Failure: Different control flow
    if depth > max_depth:
        return None
    else:
        try:
            name = acc.accName(0)
            if name and isinstance(name, str) and (len(name.strip()) > 2):
                        key = name.strip()[:200]
                        if key not in seen:
                            seen.add(key)
                            all_texts.append(name.strip())
        except:
            pass
        try:
            value = acc.accValue(0)
            if value and isinstance(value, str) and (len(value.strip()) > 2):
                        key = value.strip()[:200]
                        if key not in seen:
                            seen.add(key)
                            all_texts.append(value.strip())
        except:
            pass
        try:
            desc = acc.accDescription(0)
            if desc and isinstance(desc, str) and (len(desc.strip()) > 2):
                        key = desc.strip()[:200]
                        if key not in seen:
                            seen.add(key)
                            all_texts.append(desc.strip())
        except:
            pass
    try:
        child_count = acc.accChildCount
        if child_count > 0:
            children = (comtypes.VARIANT * child_count)()
            obtained = c_long(0)
    finally:
        comtypes.oledll.oleacc.AccessibleChildren(acc, 0, child_count, children, byref(obtained))
    for i in range(obtained.value):
        child = children[i]
        try:
            if hasattr(child, 'value') and child.vt == comtypes.automation.VT_DISPATCH:
                from comtypes.gen.Accessibility import IAccessible
                child_acc = child.value.QueryInterface(IAccessible)
                traverse_iaccessible(child_acc, all_texts, seen, depth + 1, max_depth)
            else:
                if hasattr(child, 'value') and isinstance(child.value, int):
                        child_id = child.value
                        try:
                            name = acc.accName(child_id)
                            if name and isinstance(name, str) and (len(name.strip()) > 2):
                                        key = name.strip()[:200]
                                        if key not in seen:
                                            seen.add(key)
                                            all_texts.append(name.strip())
                        except:
                            pass
                        try:
                            value = acc.accValue(child_id)
                            if value and isinstance(value, str) and (len(value.strip()) > 2):
                                        key = value.strip()[:200]
                                        if key not in seen:
                                            seen.add(key)
                                            all_texts.append(value.strip())
                        except:
                            pass
        except:
            continue
    return
def deep_iaccessible_extract(hwnd):
    """Deep IAccessible extraction - gets Chrome\'s full DOM text via COM accessibility API.\n    Also searches all child windows (Chrome renderer runs in child process windows)."""
    all_texts = []
    seen = set()
    print('  → IAccessible: Main window...')
    acc = get_iaccessible_from_hwnd(hwnd)
    if acc:
        traverse_iaccessible(acc, all_texts, seen)
        print(f'    Got {len(all_texts)} text items from main window')
    print('  → IAccessible: Scanning ALL child windows...')
    child_hwnds = []
    def collect_children(child_hwnd, _):
        child_hwnds.append(child_hwnd)
        return True
    try:
        win32gui.EnumChildWindows(hwnd, collect_children, None)
    except:
        pass
    print(f'    Found {len(child_hwnds)} child windows')
    for child_hwnd in child_hwnds:
        try:
            child_acc = get_iaccessible_from_hwnd(child_hwnd)
            if child_acc:
                before = len(all_texts)
                traverse_iaccessible(child_acc, all_texts, seen)
                after = len(all_texts)
                if after > before:
                    cls_name = ''
                    try:
                        cls_name = win32gui.GetClassName(child_hwnd)
                    except:
                        pass
                    print(f'    Child [{cls_name}]: +{after - before} text items')
        except:
            continue
    return all_texts
def extract_all_ui_text():
    """Extract ALL text from window - FORCES Chrome accessibility tree first."""
    # ***<module>.extract_all_ui_text: Failure: Different bytecode
    all_texts = []
    hwnd = win32gui.GetForegroundWindow()
    title = ''
    try:
        title = win32gui.GetWindowText(hwnd)
    except:
        pass
    print(f'  Target: \'{title}\' (hwnd={hwnd})')
    set_chrome_accessibility_registry()
    print('  → Sending WM_GETOBJECT to all windows to force accessibility...')
    OBJID_CLIENT = 4294967292
    try:
        ctypes.windll.user32.SendMessageW(hwnd, 61, 0, OBJID_CLIENT)
    except:
        pass
    child_count = [0]
    def wm_getobject_enum(child_hwnd, _):
        try:
            ctypes.windll.user32.SendMessageW(child_hwnd, 61, 0, OBJID_CLIENT)
            child_count[0] += 1
            return True
        except:
            return True
    try:
        win32gui.EnumChildWindows(hwnd, wm_getobject_enum, None)
    except:
        pass
    print(f'  → Sent WM_GETOBJECT to {child_count[0]} child windows')
    print('  → FORCING Chrome accessibility tree...')
    force_chrome_accessibility_on()
    HWND_BROADCAST = 65535
    try:
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, 26, 0, 0, 2, 5000, None)
        print('  → WM_SETTINGCHANGE broadcast sent')
    except:
        pass
    time.sleep(8)
    hwnd = win32gui.GetForegroundWindow()
    print('  → Listing child windows for diagnostics:')
    diag_children = []
    def diag_enum(child_hwnd, _):
        try:
            cls = win32gui.GetClassName(child_hwnd)
            txt = win32gui.GetWindowText(child_hwnd)
            diag_children.append((child_hwnd, cls, txt))
            return True
        except:
            return True
    try:
        win32gui.EnumChildWindows(hwnd, diag_enum, None)
    except:
        pass
    for ch_hwnd, ch_cls, ch_txt in diag_children[:20]:
        print(f'    [{ch_hwnd}] class=\'{ch_cls}\' text=\'{ch_txt[:60]}\'')
    print(f'  → Total child windows: {len(diag_children)}')
    print('  → METHOD 1: Deep IAccessible COM traversal...')
    try:
        _ensure_accessibility_typelib()
        ia_texts = deep_iaccessible_extract(hwnd)
        if ia_texts:
            all_texts.extend(ia_texts)
            print(f'  → IAccessible found {len(ia_texts)} text items!')
    except Exception as e:
        print(f'  → IAccessible failed: {e}')
    print('  → METHOD 2: UIA backend (with forced accessibility)...')
    try:
        app = Application(backend='uia').connect(handle=hwnd)
        dlg = app.window(handle=hwnd)
        seen_texts = set((t[:200] for t in all_texts))
        for c in dlg.descendants():
            try:
                text = c.window_text()
                if text and text.strip() and (len(text.strip()) > 2):
                            key = text.strip()[:200]
                            if key not in seen_texts:
                                seen_texts.add(key)
                                all_texts.append(text.strip())
            except:
                continue
        print(f'  → UIA total: {len(all_texts)} items')
    except Exception as e:
        print(f'  → UIA failed: {e}')
    print('  → METHOD 4: EnumChildWindows text...')
    try:
        seen_set = set((t[:200] for t in all_texts))
        def enum_callback(child_hwnd, _):
            # ***<module>.extract_all_ui_text.enum_callback: Failure: Compilation Error
            try:
                length = win32gui.GetWindowTextLength(child_hwnd)
                if length > 3:
                    text = win32gui.GetWindowText(child_hwnd)
                    if not text or text.strip():
                            key = text.strip()[:200]
                            if key not in seen_set:
                                seen_set.add(key)
                                all_texts.append(text.strip())
                                return True
                            else:
                                return True
                        else:
                            return True
                    else:
                        return True
                else:
                    return True
            except:
                return True
        win32gui.EnumChildWindows(hwnd, enum_callback, None)
    except Exception as e:
        print(f'  → EnumChild failed: {e}')
    force_chrome_accessibility_off()
    print(f'  → TOTAL text items collected: {len(all_texts)}')
    for i, t in enumerate(all_texts[:20]):
        print(f'    [{i}] {t[:100]}')
    return all_texts
def extract_window_text_from_foreground():
    """Master extraction function - tries multiple methods"""
    time.sleep(0.3)
    print('🔄 Phase 1: UI Automation text extraction...')
    def run_uia_and_filter(attempt_num):
        import re
        all_texts = extract_all_ui_text()
        if not all_texts:
            return None
        else:
            junk_patterns = ['Section ', 'Time Remaining', 'Answered', 'Not Visited', 'Not Answered', 'Overall Summary', 'Finish', 'Next >', 'Next', '< Previous', 'Previous', 'Mark for Review', 'Clear Response', 'Marks', 'Question Palette']
            filtered = []
            for text in all_texts:
                is_junk = False
                stripped = text.strip()
                if stripped.isdigit():
                    is_junk = True
                else:
                    if len(stripped) <= 4:
                        is_junk = True
                    else:
                        if re.fullmatch('[\\d\\s]+', stripped) and len(stripped) > 8:
                            is_junk = True
                        else:
                            if stripped.startswith('http://') or stripped.startswith('https://') or stripped.startswith('file://'):
                                is_junk = True
                            else:
                                for pattern in junk_patterns:
                                    if stripped.lower() == pattern.lower():
                                        is_junk = True
                                        break
                if not is_junk:
                    filtered.append(stripped)
            focused = None
            for i, item in enumerate(filtered):
                if 'select the correct answer' in item.lower() or item.lower() == 'select the correct answer':
                    block = filtered[i:i + 8]
                    focused = '\n'.join(block)
                    break
            if focused is None:
                for i, item in enumerate(filtered):
                    if re.match('Question \\d+ of \\d+', item):
                        block = filtered[max(0, i - 1):i + 12]
                        focused = '\n'.join(block)
                        break
            if focused and len(focused) > 30:
                return focused
            else:
                full_text = '\n'.join(filtered)
                if len(full_text) > 200:
                    return full_text[:3000]
                else:
                    print(f'  → Attempt {attempt_num}: UIA got {len(full_text)} chars (Chrome tree not ready yet)...')
                    return None
    full_text = run_uia_and_filter(1)
    if full_text is None:
        print('  ⏳ Waiting 10s for Chrome accessibility tree to build, then retrying...')
        time.sleep(10)
        full_text = run_uia_and_filter(2)
    if full_text:
        is_coding = None
        if 'Section 2 of 2' in full_text:
            is_coding = True
        else:
            if 'select the correct answer' in full_text.lower():
                is_coding = False
        print(f'✅ UI extraction got {len(full_text)} chars')
        return (full_text, is_coding)
    else:
        print('❌ All methods failed!')
        return ('❌ Could not capture question.\n\nTry again (Alt+A) — Chrome needs ~10s to build accessibility tree on first use.', False)
class ExtractThread(QThread):
    finished = pyqtSignal(str, object)
    error = pyqtSignal(str)
    def run(self):
        # irreducible cflow, using cdg fallback
        # ***<module>.ExtractThread.run: Failure: Compilation Error
        pythoncom.CoInitialize()
        try:
            pass
        finally:
            text, is_coding = extract_window_text_from_foreground()
        self.finished.emit(text, is_coding)
        except Exception as e:
            pass
        self.error.emit(str(e))
        pythoncom.CoUninitialize()
class LoginDialog(QDialog):
    def __init__(self, hwid):
        super().__init__()
        self.hwid = hwid
        self.setWindowTitle('Authorization Required')
        self.setFixedSize(420, 260)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet('\n            QDialog { background-color: #f5f5f5; color: #333; }\n            QLabel { color: #333; font-size: 10pt; }\n            QLineEdit { background: white; color: #333; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-family: Consolas; font-size: 9pt; }\n            QPushButton { background: #4a4a4a; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px; border: none; }\n            QPushButton:hover { background: #333; }\n        ')
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel('Device Not Authorized')
        title.setStyleSheet('color: #333; font-weight: bold; font-size: 13pt;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(QLabel('Your Device ID:'))
        hwid_layout = QHBoxLayout()
        self.hwid_input = QLineEdit(self.hwid)
        self.hwid_input.setReadOnly(True)
        self.hwid_input.setSelection(0, len(self.hwid))
        hwid_layout.addWidget(self.hwid_input)
        self.copy_btn = QPushButton('Copy')
        self.copy_btn.setFixedWidth(70)
        self.copy_btn.clicked.connect(self.copy_id)
        hwid_layout.addWidget(self.copy_btn)
        layout.addLayout(hwid_layout)
        self.status_label = QLabel('Send this ID to Admin for access')
        self.status_label.setStyleSheet('color: #666; font-size: 9pt;')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        self.check_btn = QPushButton('Check Status')
        self.check_btn.clicked.connect(self.check_access)
        layout.addWidget(self.check_btn)
        self.setLayout(layout)
        QTimer.singleShot(100, self.auto_copy_hwid)
    def auto_copy_hwid(self):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(self.hwid, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            self.status_label.setText('ID auto-copied! Send to Admin for access')
            self.copy_btn.setText('Copied!')
            QTimer.singleShot(2000, lambda: self.copy_btn.setText('Copy'))
        except:
            self.status_label.setText('Select ID & press Ctrl+C to copy')
    def copy_id(self):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(self.hwid, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            self.copy_btn.setText('Copied!')
            self.status_label.setText('ID copied to clipboard!')
            QTimer.singleShot(2000, lambda: self.copy_btn.setText('Copy'))
        except Exception as e:
            self.status_label.setText('Copy failed - select & Ctrl+C manually')
    def check_access(self):
        # Authentication bypassed - auto-grant access
        self.check_btn.setText('Checking...')
        self.check_btn.setEnabled(False)
        self.status_label.setText('Checking...')
        QApplication.processEvents()
        # Auto-grant without server check
        self.status_label.setText('Access Granted!')
        self.status_label.setStyleSheet('color: green; font-size: 9pt; font-weight: bold;')
        QTimer.singleShot(500, self.accept)
class ChatbotThread(QThread):
    response_ready = pyqtSignal(str, object)
    stats_ready = pyqtSignal(int, int)
    def __init__(self, prompt, hwid, is_coding):
        super().__init__()
        self.prompt = prompt
        self.hwid = hwid
        self.is_coding = is_coding
    def run(self):
        # irreducible cflow, using cdg fallback
        # ***<module>.ChatbotThread.run: Failure: Compilation Error
        pythoncom.CoInitialize()
        try:
            pass
        finally:
            payload = {'hwid': self.hwid, 'app_id': APP_ID_LPU, 'api_token': API_TOKEN_LPU, 'message': self.prompt, 'images': []}
            gen_response = session.post(GENERATE_URL, json=payload, timeout=45)
            if gen_response.status_code == 200:
                data = gen_response.json()
                if data.get('success'):
                    answer = data.get('answer', '')
                    clean_res = answer.replace('```python', '').replace('```sql', '').replace('```html', '').replace('```', '').strip()
                    stats = data.get('stats', {})
                    if 'limit' in stats and 'used' in stats:
                            self.stats_ready.emit(stats['limit'], stats['used'])
                    self.response_ready.emit(clean_res, self.is_coding)
                else:
                    self.response_ready.emit(f"Server Error: {data.get('error', 'Unknown Error')}", False)
            else:
                try:
                    err_json = gen_response.json()
                    err_msg = err_json.get('error', 'Unknown Error')
                    if gen_response.status_code == 401:
                        self.response_ready.emit(f'ACCESS DENIED.\nHWID: {self.hwid}\nMessage: {err_msg}', False)
                    else:
                        if gen_response.status_code == 403:
                            self.response_ready.emit(f'LICENSE ERROR: {err_msg}', False)
                        else:
                            self.response_ready.emit(f'API Error ({gen_response.status_code}): {err_msg}', False)
                except:
                    self.response_ready.emit(f'HTTP Error: {gen_response.status_code}', False)
        except Exception as e:
            pass
        self.response_ready.emit('Connection error. Check internet & try again.', False)
        pythoncom.CoUninitialize()
def set_window_exclude_from_capture(hwnd):
    try:
        WDA_EXCLUDEFROMCAPTURE = 17
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    except:
        return None
class ChatbotUI(QWidget):
    def __init__(self, hwid):
        super().__init__()
        self.hwid = hwid
        self.cursor_mode_pending = False
        self.cursor_mode_enabled = False
        self.cursor_min_confidence = 65
        self.cursor_double_check_enabled = True
        self.cursor_check_stage = 0
        self.cursor_first_answer = None
        self.cursor_question_text = ''
        if not self.verify_device_startup():
            sys.exit()
        self.is_coding = None
        self.system_active = False
        self.setup_ui()
    def verify_device_startup(self):
        """Device authorization bypassed - auto-allow startup."""
        # Authentication removed - auto-grant access
        return True
    def protect_from_screen_recording(self):
        try:
            set_window_exclude_from_capture(int(self.winId()))
        except Exception as e:
            print(f'Screen recording protection error: {e}')
    def setup_ui(self):
        self.setWindowTitle('LPU Nest Helper - MCQ Cursor Mode')
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowOpacity(0.55)
        self.setStyleSheet('background-color: #fafafa; border: 1px solid #ccc;')
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'setting_ico.ico')
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                self.setWindowIcon(QIcon(icon_path))
                print(f'[UI] Window icon loaded: {icon_path}')
        except Exception as e:
            print(f'[UI] Icon load warning: {e}')
        self.resize(280, 330)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 100, screen.height() - self.height() - 50)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.label = QLabel(f'<b>LPU Helper | ID: {self.hwid[:8]}...</b><br><span style=\'color:#555; font-size:8px;\'>Alt+X: <span style=\'color:red;font-weight:bold;\'>OFF</span> | Alt+d: Hide | Alt+A: Vision | Alt+M: MCQ Cursor | Alt+Shift+W: Type</span>', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('color: #444; font-size: 8px; padding: 2px; border: 1px solid #ddd; border-radius: 3px;')
        self.layout.addWidget(self.label)
        self.stats_label = QLabel('Status: Checking...')
        self.stats_label.setStyleSheet('color: #333; font-size: 10px; background: #e8e8e8; padding: 5px; border-radius: 3px;')
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.stats_label)
        pause_thread = threading.Thread(target=check_pause, daemon=True)
        pause_thread.start()
        self.text_input = QTextEdit(self)
        self.text_input.setPlaceholderText('Question will appear here...')
        self.text_input.setStyleSheet('background: white; border: 1px solid #ddd; color: #333; font-size: 10px;')
        self.layout.addWidget(self.text_input)
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setPlaceholderText('Answer will appear here...')
        self.output.setStyleSheet('background: white; border: 1px solid #ddd; color: #333; font-size: 10px;')
        self.layout.addWidget(self.output)
        self.copy_id_btn = QPushButton('Copy ID', self)
        self.copy_id_btn.clicked.connect(self.copy_hwid)
        self.copy_id_btn.setStyleSheet('background-color: #e0e0e0; border: 1px solid #ccc; color: #333; font-size: 9px; padding: 4px; border-radius: 3px;')
        self.copy_id_btn.setToolTip(f'HWID: {self.hwid}')
        self.layout.addWidget(self.copy_id_btn)
        self.setLayout(self.layout)
        self.send_timer = QTimer(self)
        self.send_timer.setSingleShot(True)
        self.send_timer.timeout.connect(self.get_response)
        self.hide()
        self.protect_from_screen_recording()
        self.start_global_key_listener()
    def update_stats(self, limit, used):
        remaining = limit - used
        if remaining > 0:
            self.stats_label.setText(f'Active | Remaining: {remaining}/{limit}')
            self.stats_label.setStyleSheet('color: #2a7a2a; font-size: 10px; background: #e8f5e8; padding: 5px; border-radius: 3px;')
        else:
            self.stats_label.setText(f'Limit Reached ({used}/{limit})')
            self.stats_label.setStyleSheet('color: #a00; font-size: 10px; background: #ffe8e8; padding: 5px; border-radius: 3px;')
    def copy_hwid(self):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(self.hwid, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            self.copy_id_btn.setText('Copied!')
            QTimer.singleShot(1500, lambda: self.copy_id_btn.setText('Copy ID'))
        except:
            return None
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos:
                delta = event.globalPos() - self.old_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_pos = event.globalPos()
    def showEvent(self, event):
        super().showEvent(event)
        try:
            set_window_exclude_from_capture(int(self.winId()))
        except:
            return None
    def _wrap_action(self, action_func, requires_active=True):
        def wrapper():
            if requires_active and (not self.system_active):
                    return None
            QTimer.singleShot(0, action_func)
        return wrapper
    def _toggle_visibility_action(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
    def _auto_type_action(self):
        self.hide()
        QTimer.singleShot(200, self.trigger_auto_typer)
    def _alt_m_action(self):
        self.cursor_mode_pending = True
        self.cursor_check_stage = 0
        self.cursor_first_answer = None
        self.cursor_question_text = ''
        print('[Cursor] Alt+M mode activated')
        QTimer.singleShot(0, self.get_window_text)
    def start_global_key_listener(self):
        keyboard.add_hotkey('alt+x', self._wrap_action(self.toggle_system, False), suppress=True)
        keyboard.add_hotkey('alt+d', self._wrap_action(self._toggle_visibility_action, True), suppress=True)
        keyboard.add_hotkey('alt+shift+w', self._wrap_action(self._auto_type_action, True), suppress=True)
        keyboard.add_hotkey('alt+a', self._wrap_action(self.get_window_text, True), suppress=True)
        keyboard.add_hotkey('alt+c', self._wrap_action(self.read_from_clipboard, True), suppress=True)
        keyboard.add_hotkey('alt+m', self._wrap_action(self._alt_m_action, True), suppress=True)
        keyboard.add_hotkey('alt+shift+p', toggle_pause, suppress=True)
    def get_window_text(self):
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '📸 Capturing screen... Please wait...'))
        if hasattr(self, 'extract_thread') and self.extract_thread.isRunning():
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Already processing... Please wait.'))
            return None
        else:
            self.hide()
            time.sleep(0.3)
            self.extract_thread = ExtractThread()
            self.extract_thread.finished.connect(self.handle_window_text)
            self.extract_thread.error.connect(self.display_error)
            self.extract_thread.start()
    def read_from_clipboard(self):
        """Backup method: Read question from clipboard (manual copy-paste)"""
        try:
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            if text and len(text.strip()) > 10:
                self.text_input.setPlainText(text.strip())
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '✓ Clipboard text loaded! Processing...'))
                self.is_coding = None
                self.start_send_timer()
            else:
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '⚠️ Clipboard is empty or too short!\n\nCopy question text first (Ctrl+C)'))
        except Exception as e:
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, f'❌ Clipboard error: {e}\n\nMake sure you copied text first!'))
    def handle_window_text(self, text, is_coding):
        self.is_coding = is_coding
        if not self.cursor_mode_pending:
            self.show()
        if not text or len(text.strip()) < 10:
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '⚠️ No question detected!\n\nTips:\n1. Make sure question is visible on screen\n2. Wait for page to fully load\n3. Try pressing Alt+A again\n4. Maximize browser window'))
            return None
        else:
            self.text_input.setPlainText(text)
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '✓ Question captured! Processing...'))
            self.start_send_timer()
    def start_send_timer(self):
        self.send_timer.start(500)
    def get_response(self):
        user_input = self.text_input.toPlainText().strip()
        if user_input:
            if hasattr(self, 'worker') and self.worker.isRunning():
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Processing... Please wait.'))
                return None
            else:
                if self.cursor_mode_pending:
                    self.cursor_question_text = user_input
                    user_input = self.build_cursor_prompt(self.cursor_question_text, second_pass=False)
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Connecting to Server...'))
                self.worker = ChatbotThread(user_input, self.hwid, self.is_coding)
                self.worker.response_ready.connect(self.display_response)
                self.worker.stats_ready.connect(self.update_stats)
                self.worker.start()
    def build_cursor_prompt(self, question_text, second_pass=False):
        instruction = 'Return ONLY in this exact format:\nFINAL_ANSWER: <A/B/C/D>\nCONFIDENCE: <0-100>\nREASON: <one short line>'
        if second_pass:
            instruction += '\n\nRe-evaluate independently from scratch. Do not reuse any previous answer.'
        return f'{question_text}\n\n{instruction}'
    def reset_cursor_mode_state(self):
        self.cursor_mode_pending = False
        self.cursor_check_stage = 0
        self.cursor_first_answer = None
        self.cursor_question_text = ''
    def start_cursor_verification_pass(self):
        if not self.cursor_question_text:
            self.reset_cursor_mode_state()
            return None
        else:
            if hasattr(self, 'worker') and self.worker.isRunning():
                QTimer.singleShot(200, self.start_cursor_verification_pass)
                return None
            else:
                verify_prompt = self.build_cursor_prompt(self.cursor_question_text, second_pass=True)
                self.worker = ChatbotThread(verify_prompt, self.hwid, self.is_coding)
                self.worker.response_ready.connect(self.display_response)
                self.worker.stats_ready.connect(self.update_stats)
                self.worker.start()
    def extract_mcq_answer(self, response_text):
        if not response_text:
            return None
        else:
            answer_upper = response_text.upper()
            patterns = ['(?:ANSWER|OPTION|CORRECT)[\\s:=-]*([ABCD])', '\\b([ABCD])\\)', '\\b([ABCD])\\b', '([ABCD])']
            for pattern in patterns:
                matches = re.findall(pattern, answer_upper)
                if matches:
                    return matches[(-1)]
            return None
    def extract_mcq_confidence(self, response_text):
        if not response_text:
            return None
        else:
            m = re.search('CONFIDENCE\\s*[:=-]\\s*(\\d{1,3})', response_text, re.IGNORECASE)
            if m:
                value = int(m.group(1))
                return max(0, min(100, value))
            else:
                p = re.search('\\b(\\d{1,3})\\s*%', response_text)
                if p:
                    value = int(p.group(1))
                    return max(0, min(100, value))
                else:
                    return None
    def is_probable_mcq_question(self, text):
        if not text:
            return False
        else:
            t = text.upper()
            markers = ['SELECT THE CORRECT ANSWER', 'OPTION', ' A)', ' B)', ' C)', ' D)', ' A.', ' B.', ' C.', ' D.', 'WHICH', 'WHAT', 'WHO', 'WHERE', 'WHEN', 'WHY', 'HOW']
            if any((m in t for m in markers)):
                print('[MCQ] Detected via explicit marker')
                return True
            else:
                lowercase_pattern = '\\b[a-d]\\)|\\b[a-d]\\.'
                lowercase_matches = re.findall(lowercase_pattern, text)
                if len(lowercase_matches) >= 3:
                    print(f'[MCQ] Detected via lowercase options: {lowercase_matches}')
                    return True
                else:
                    uppercase_pattern = '\\b[A-D]\\)|\\b[A-D]\\.'
                    uppercase_matches = re.findall(uppercase_pattern, text)
                    if len(uppercase_matches) >= 3:
                        print(f'[MCQ] Detected via uppercase options: {uppercase_matches}')
                        return True
                    else:
                        radio_pattern = '\\(\\s*\\)|\\[\\s*\\]|☐|○|●'
                        radio_matches = re.findall(radio_pattern, text)
                        if len(radio_matches) >= 3:
                            print(f'[MCQ] Detected via radio/checkbox: {len(radio_matches)} buttons')
                            return True
                        else:
                            lines = text.split('\n')
                            if len(lines) >= 4:
                                first_line = lines[0].upper()
                                question_starters = ['WHICH', 'WHAT', 'WHO', 'WHERE', 'WHEN', 'WHY', 'HOW', 'IF ', 'WILL ', 'CAN ', 'DOES ', 'DID ', 'IS ', 'ARE ']
                                for starter in question_starters:
                                    if first_line.startswith(starter):
                                        print(f'[MCQ] Detected via generic question pattern: {starter}')
                                        return True
                            print(f'[MCQ] Not detected. Text preview: {text[:100]}')
                            return False
    def should_move_cursor(self, response_text):
        """Return tuple: (can_move, answer, reason_text)."""
        question_text = self.text_input.toPlainText()
        if not self.is_probable_mcq_question(question_text):
            return (False, None, 'Skipped: question doesn\'t look like MCQ')
        else:
            response_upper = response_text.upper()
            answer_choice = None
            m = re.search('FINAL_ANSWER\\s*[:=-]\\s*([ABCD])', response_upper)
            if m:
                answer_choice = m.group(1)
                print(f'[Cursor] Answer from FINAL_ANSWER: {answer_choice}')
            if not answer_choice:
                m = re.search('(?:ANSWER|OPTION|CORRECT)\\s*[:=-]\\s*([ABCD])', response_upper)
                if m:
                    answer_choice = m.group(1)
                    print(f'[Cursor] Answer from ANSWER/OPTION/CORRECT: {answer_choice}')
            if not answer_choice:
                for letter in ['A', 'B', 'C', 'D']:
                    pattern = f'\\b{letter}\\)'
                    matches = re.findall(pattern, response_upper)
                    if matches and len(matches) == 1:
                            answer_choice = letter
                            print(f'[Cursor] Answer from isolated {letter}): {answer_choice}')
                            break
            if not answer_choice:
                unique_letters = set()
                for letter in ['A', 'B', 'C', 'D']:
                    if letter in response_upper:
                        unique_letters.add(letter)
                if len(unique_letters) == 1:
                    answer_choice = list(unique_letters)[0]
                    print(f'[Cursor] Answer from single letter detection: {answer_choice}')
            if not answer_choice:
                return (False, None, 'Skipped: no A/B/C/D answer found')
            else:
                confidence = self.extract_mcq_confidence(response_text)
                if confidence is None:
                    confidence = 80
                if confidence < self.cursor_min_confidence:
                    return (False, None, f'Skipped: low confidence ({confidence}%)')
                else:
                    return (True, answer_choice, 'OK')
    def move_cursor_to_mcq_corner(self, answer_choice):
        if answer_choice not in ['A', 'B', 'C', 'D']:
            return False
        else:
            try:
                sw = win32api.GetSystemMetrics(0)
                sh = win32api.GetSystemMetrics(1)
                positions = {'A': (0, 0), 'B': (sw - 1, 0), 'C': (0, sh - 1), 'D': (sw - 1, sh - 1)}
                target_x, target_y = positions[answer_choice]
                duration = 0.8
                steps = 50
                sleep_time = duration / steps
                try:
                    start_x, start_y = win32api.GetCursorPos()
                except:
                    start_x, start_y = (sw // 2, sh // 2)
                for i in range(1, steps + 1):
                    t = i / steps
                    if t < 0.5:
                        ease = 2 * t * t
                    else:
                        ease = (-1) + (4 - 2 * t) * t
                    cur_x = int(start_x + (target_x - start_x) * ease)
                    cur_y = int(start_y + (target_y - start_y) * ease)
                    win32api.SetCursorPos((cur_x, cur_y))
                    time.sleep(sleep_time)
                win32api.SetCursorPos((target_x, target_y))
                return True
            except Exception as e:
                print(f'Cursor move failed: {e}')
                return False
    def display_response(self, response, is_coding):
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, response))
        self.last_response = response
        if self.cursor_mode_pending:
            print(f'[Cursor] Stage {self.cursor_check_stage}: Processing response...')
            can_move, answer_choice, reason = self.should_move_cursor(response)
            print(f'[Cursor] can_move={can_move}, answer={answer_choice}, reason={reason}')
            if not can_move or not answer_choice:
                self.cursor_mode_enabled = False
                self.reset_cursor_mode_state()
                QMetaObject.invokeMethod(self.output, 'append', Qt.QueuedConnection, Q_ARG(str, f'\n⚠ Cursor not moved: {reason}'))
                return None
            else:
                if self.cursor_double_check_enabled and self.cursor_check_stage == 0:
                    self.cursor_first_answer = answer_choice
                    self.cursor_check_stage = 1
                    print(f'[Cursor] First pass answer: {answer_choice}, starting verification pass...')
                    QMetaObject.invokeMethod(self.output, 'append', Qt.QueuedConnection, Q_ARG(str, f'\nℹ First pass: {answer_choice}. Verifying...'))
                    self.start_cursor_verification_pass()
                    return None
                else:
                    if self.cursor_double_check_enabled and self.cursor_check_stage == 1:
                            print(f'[Cursor] Second pass answer: {answer_choice}, comparing with first: {self.cursor_first_answer}')
                            if answer_choice!= self.cursor_first_answer:
                                self.cursor_mode_enabled = False
                                first_ans = self.cursor_first_answer
                                self.reset_cursor_mode_state()
                                QMetaObject.invokeMethod(self.output, 'append', Qt.QueuedConnection, Q_ARG(str, f'\n⚠ Cursor not moved: mismatch ({first_ans} vs {answer_choice})'))
                                return None
                            else:
                                print(f'[Cursor] Verification passed, moving cursor to {answer_choice}...')
                    if can_move and answer_choice and self.move_cursor_to_mcq_corner(answer_choice):
                        self.cursor_mode_enabled = True
                        self.reset_cursor_mode_state()
                        print(f'[Cursor] SUCCESS: Cursor moved to {answer_choice}')
                        QMetaObject.invokeMethod(self.output, 'append', Qt.QueuedConnection, Q_ARG(str, f'\n✓ Cursor moved for answer: {answer_choice} (double-check passed)'))
                    else:
                        self.cursor_mode_enabled = False
                        self.reset_cursor_mode_state()
                        print('[Cursor] FAILED: Could not move cursor')
                        QMetaObject.invokeMethod(self.output, 'append', Qt.QueuedConnection, Q_ARG(str, f'\n⚠ Cursor not moved: {reason}'))
    def trigger_auto_typer(self):
        if hasattr(self, 'last_response'):
            typer_thread = threading.Thread(target=lambda: auto_typer(self.last_response), daemon=True)
            typer_thread.start()
    def display_error(self, error_message):
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, f'Error: {error_message}'))
    def toggle_system(self):
        """Toggle system on/off with Alt+X"""
        self.system_active = not self.system_active
        status_text = 'ACTIVE' if self.system_active else 'OFF'
        status_color = 'green' if self.system_active else 'red'
        new_label = f'<b>LPU Helper | ID: {self.hwid[:8]}...</b><br><span style=\'color:#555; font-size:8px;\'>Alt+X: <span style=\'color:{status_color};font-weight:bold;\'>{status_text}</span> | Alt+d: Hide | Alt+A: Vision | Alt+M: MCQ Cursor | Alt+Shift+W: Type</span>'
        self.label.setText(new_label)
        self.stats_label.setText(f'SYSTEM {status_text}')
        self.stats_label.setStyleSheet(f'color: {status_color}; font-size: 10px; background: #eee; padding: 5px; border-radius: 3px; font-weight: bold;')
        if self.system_active:
            self.show()
            def warmup_a11y():
                try:
                    set_chrome_accessibility_registry()
                    force_chrome_accessibility_on()
                    print('🔧 Accessibility warmed up for active session')
                except:
                    return None
            threading.Thread(target=warmup_a11y, daemon=True).start()
        else:
            self.hide()
if __name__ == '__main__':
    mutex_name = 'Global\\GeminiNesBot_SingleInstance_Mutex'
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    if last_error == 183:
        error_app = QApplication(sys.argv)
        QMessageBox.warning(None, 'Already Running', 'It\'s already running. To avoid multiple instances, this launch will close.')
        sys.exit(0)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    my_hwid = get_stable_hwid()
    print(f'App Started. HWID: {my_hwid}')
    print('🔧 Startup: Pre-warming Chrome accessibility...')
    set_chrome_accessibility_registry()
    force_chrome_accessibility_on()
    print('🔧 Accessibility pre-warmed. First Alt+A should work now!')
    window = ChatbotUI(my_hwid)
    app._instance_mutex = mutex
    sys.exit(app.exec_())
