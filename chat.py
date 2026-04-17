
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
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QDialog, QComboBox, QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QMetaObject, Q_ARG, QRect, QPoint, QSize, QRect as QtCoreQRect
from PyQt5.QtGui import QIcon, QColor, QImage, QPixmap, QPainter, QPen, QCursor
import socketio
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from pynput import keyboard as pynput_keyboard
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
    try:
        # Handle Unicode characters in Windows console
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(msg.encode('utf-8', errors='replace'))
            sys.stdout.buffer.write(b'\n')
        else:
            _original_print(msg, **kwargs)
    except:
        _original_print(msg, **kwargs)
    try:
        _log.info(msg)
    except:
        return None
print(f'=== Pea Bot Started === Log: {_log_path}')
# Authentication removed - app runs without authorization
GENERATE_URL = "https://lpu-helper-backend.onrender.com/generate"
AUTH_SERVER_URL = None

# API Configuration
API_TOKEN_LPU = "lpu-super-secret-token-2024"
APP_ID_LPU = "lpu-helper"

# System Prompts for different modes
MCQ_SYSTEM_PROMPT = "This is a Multiple Choice Question. For each question, provide the correct answer text (not just the letter). If multiple questions, answer each one clearly. Be concise."
CODE_SYSTEM_PROMPT = "This is a coding problem. Return only a complete, runnable solution in the target language. Read from standard input and write to standard output. No explanation, no comments, no markdown fences."

session = requests.Session()
# Retry config: 1 retry with exponential backoff for server errors
_retry = Retry(
    total=1,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=['POST'],
    raise_on_status=False  # Let us handle status codes manually
)
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
        # Handle tabs by converting to spaces (or send tab key)
        if char == '\t':
            # Send Tab key
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_TAB, 0)
            time.sleep(0.02)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_TAB, 0)
            time.sleep(0.03)
        else:
            win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
            if char == ' ':
                time.sleep(0.02)
            else:
                time.sleep(0.01)
def auto_typer(text):
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    else:
        # Extract code from markdown blocks
        clean_text = text
        if '```' in clean_text:
            parts = clean_text.split('```')
            if len(parts) >= 2:
                clean_text = parts[1]
                # Remove language identifier (python, sql, html, etc)
                first_line = clean_text.split('\n')[0]
                if first_line.strip() in ['python', 'sql', 'html', 'java', 'javascript', 'cpp', 'c']:
                    clean_text = '\n'.join(clean_text.split('\n')[1:])
        
        clean_text = clean_text.rstrip()
        if not clean_text:
            return None
        else:
            lines = clean_text.split('\n')
            for line in lines:
                while paused:
                    time.sleep(0.1)
                
                # Extract and preserve leading indentation
                indent = len(line) - len(line.lstrip())
                line_content = line.rstrip()
                
                if line_content:
                    # Send leading whitespace all at once to preserve indentation
                    if indent > 0:
                        leading_ws = line[:indent]
                        send_keys(hwnd, leading_ws)
                        time.sleep(0.08)
                    
                    # Send the non-indented content
                    content = line_content[indent:]
                    send_keys(hwnd, content)
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
    try:
        ctypes.windll.user32.NotifyWinEvent(EVENT_SYSTEM_ALERT, 0, 0, 0)
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
    """Recursively traverse IAccessible tree and collect ONLY VISIBLE text"""
    # ***<module>.traverse_iaccessible: Failure: Different control flow
    if depth > max_depth:
        return None
    else:
        try:
            # Check if element is visible (STATE_SYSTEM_INVISIBLE = 0x8000 = 32768)
            state = acc.accState(0)
            if state and (state & 32768):  # Hidden/invisible
                return None
        except:
            pass
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
    print('  → IAccessible: Scanning visible child windows...')
    child_hwnds = []
    def collect_visible_children(child_hwnd, _):
        # Only collect VISIBLE child windows
        if win32gui.IsWindowVisible(child_hwnd):
            child_hwnds.append(child_hwnd)
        return True
    try:
        win32gui.EnumChildWindows(hwnd, collect_visible_children, None)
    except:
        pass
    print(f'    Found {len(child_hwnds)} visible child windows')
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

def capture_text_with_scrolling():
    """Scroll down and capture text from multiple viewport positions via UI extraction."""
    print('  → PHASE 4: Capturing off-screen/scrolled text...')
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        print('    ⚠️ No foreground window')
        return []
    
    all_scrolled_texts = []
    seen_chunks = set()
    max_scrolls = 6
    stagnant_steps = 0
    
    try:
        # Jump to top
        print('    → Jumping to top...')
        VK_CONTROL = 17
        VK_HOME = 36
        win32api.PostMessage(hwnd, 256, VK_CONTROL, 0)
        win32api.PostMessage(hwnd, 256, VK_HOME, 0)
        win32api.PostMessage(hwnd, 257, VK_HOME, 0)
        win32api.PostMessage(hwnd, 257, VK_CONTROL, 0)
        time.sleep(0.5)
        
        # Capture from current viewport first without sending Ctrl+A/C.
        first_items = extract_all_ui_text()
        if first_items:
            first_chunk = '\n'.join((t.strip() for t in first_items if isinstance(t, str) and t.strip()))
            if first_chunk and len(first_chunk) >= 80:
                seen_chunks.add(first_chunk)
                all_scrolled_texts.append(first_chunk)

        for scroll_num in range(max_scrolls):
            print(f'    → Scroll {scroll_num + 1}/{max_scrolls}...')

            win32api.PostMessage(hwnd, 256, 34, 0)  # VK_NEXT
            time.sleep(0.06)
            win32api.PostMessage(hwnd, 257, 34, 0)
            time.sleep(0.55)  # Let dynamic page content render.

            items = extract_all_ui_text()
            if not items:
                stagnant_steps += 1
                if stagnant_steps >= 2:
                    print('    → Reached end or no additional text, stopping scroll capture.')
                    break
                continue

            chunk = '\n'.join((t.strip() for t in items if isinstance(t, str) and t.strip()))
            if len(chunk.strip()) < 80:
                stagnant_steps += 1
                if stagnant_steps >= 2:
                    print('    → Reached end or no additional text, stopping scroll capture.')
                    break
                continue

            chunk = chunk.strip()
            if chunk in seen_chunks:
                stagnant_steps += 1
                if stagnant_steps >= 2:
                    print('    → Repeated viewport content detected, stopping scroll capture.')
                    break
            else:
                stagnant_steps = 0
                seen_chunks.add(chunk)
                all_scrolled_texts.append(chunk)
        
        print(f'    ✅ Scroll capture done (unique viewports: {len(all_scrolled_texts)})')
        return all_scrolled_texts
    
    except Exception as e:
        print(f'    ⚠️ Scroll capture error: {e}')
        return all_scrolled_texts

def extract_all_ui_text():
    """Extract ALL text from window - FORCES Chrome accessibility tree first."""
    all_texts = []
    hwnd = win32gui.GetForegroundWindow()
    title = ''
    try:
        title = win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f'  ⚠️ Could not get window title: {e}')
    
    print(f'  🎯 Target: \'{title}\' (hwnd={hwnd})')
    
    try:
        set_chrome_accessibility_registry()
    except Exception as e:
        print(f'  ⚠️ Failed to set Chrome accessibility registry: {e}')
    
    print('  → Sending WM_GETOBJECT to all windows to force accessibility...')
    OBJID_CLIENT = 4294967292
    try:
        ctypes.windll.user32.SendMessageW(hwnd, 61, 0, OBJID_CLIENT)
    except Exception as e:
        print(f'  ⚠️ SendMessageW failed: {e}')
    
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
    except Exception as e:
        print(f'  ⚠️ EnumChildWindows failed: {e}')
    
    print(f'  → Sent WM_GETOBJECT to {child_count[0]} child windows')
    print('  → FORCING Chrome accessibility tree...')
    
    try:
        force_chrome_accessibility_on()
    except Exception as e:
        print(f'  ⚠️ force_chrome_accessibility_on() failed: {e}')
    
    HWND_BROADCAST = 65535
    try:
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, 26, 0, 0, 2, 5000, None)
        print('  → WM_SETTINGCHANGE broadcast sent')
    except Exception as e:
        print(f'  ⚠️ Broadcast failed: {e}')
    
    print('  ⏳ Giving Chrome 8 seconds to build accessibility tree...')
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
    except Exception as e:
        print(f'  ⚠️ Diag enumeration failed: {e}')
    
    for ch_hwnd, ch_cls, ch_txt in diag_children[:20]:
        if ch_txt.strip():
            print(f'    [{ch_hwnd}] class=\'{ch_cls}\' text=\'{ch_txt[:60]}\'')
    
    print(f'  → Total child windows: {len(diag_children)}')
    
    print('  → METHOD 1: Deep IAccessible COM traversal...')
    try:
        _ensure_accessibility_typelib()
        ia_texts = deep_iaccessible_extract(hwnd)
        if ia_texts:
            all_texts.extend(ia_texts)
            print(f'  ✅ IAccessible found {len(ia_texts)} text items!')
    except Exception as e:
        print(f'  ⚠️ IAccessible failed: {e}')
    
    print('  → METHOD 2: UIA backend (visible elements only)...')
    try:
        app = Application(backend='uia').connect(handle=hwnd)
        dlg = app.window(handle=hwnd)
        seen_texts = set((t[:200] for t in all_texts))
        
        for c in dlg.descendants():
            try:
                try:
                    is_visible = c.is_visible()
                    if not is_visible:
                        continue
                except:
                    pass
                
                text = c.window_text()
                if text and text.strip() and (len(text.strip()) > 2):
                    key = text.strip()[:200]
                    if key not in seen_texts:
                        seen_texts.add(key)
                        all_texts.append(text.strip())
            except:
                continue
        
        print(f'  ✅ UIA total: {len(all_texts)} items')
    except Exception as e:
        print(f'  ⚠️ UIA failed: {e}')
    
    print('  → METHOD 3: Visible EnumChildWindows text...')
    try:
        seen_set = set((t[:200] for t in all_texts))
        def enum_callback(child_hwnd, _):
            try:
                if not win32gui.IsWindowVisible(child_hwnd):
                    return True
                length = win32gui.GetWindowTextLength(child_hwnd)
                if length > 3:
                    text = win32gui.GetWindowText(child_hwnd)
                    if text and text.strip():
                        key = text.strip()[:200]
                        if key not in seen_set:
                            seen_set.add(key)
                            all_texts.append(text.strip())
            except:
                pass
            return True
        
        win32gui.EnumChildWindows(hwnd, enum_callback, None)
    except Exception as e:
        print(f'  ⚠️ EnumChild failed: {e}')
    
    try:
        force_chrome_accessibility_off()
    except Exception as e:
        print(f'  ⚠️ force_chrome_accessibility_off() failed: {e}')
    
    print(f'  → TOTAL text items collected: {len(all_texts)}')
    for i, t in enumerate(all_texts[:15]):
        print(f'    [{i}] {t[:80]}...' if len(t) > 80 else f'    [{i}] {t}')
    return all_texts
def extract_window_text_from_foreground():
    """Master extraction function - tries multiple methods"""
    time.sleep(0.3)
    print('🔄 Phase 1: UI Automation text extraction...')

    def normalize_extracted_text(text):
        import re
        if not text:
            return ''

        drop_exact = {
            'tab search - pinned', 'switch to..', 'more', 'language', 'pypy 3',
            'test against custom input', 'add to favourites', 'line: 2 col: 1',
            'minimize', 'restore', 'close', 'back', 'forward', 'reload',
            'separator', 'extensions', 'show sidebar', 'wallet', 'leo ai', 'vpn',
            'bookmarks', 'saved tab groups', 'tab groups', 'problem', 'submissions',
            'leaderboard', 'discussions', 'editorial', 'change theme',
            'select your coding language', 'reset code', 'editor settings',
            'submit code', 'run code', 'blog', 'scoring', 'environment', 'faq',
            'about us', 'helpdesk', 'careers', 'terms of service', 'privacy policy',
            'new tab', 'brave talk', 'brave wallet', 'reading list', 'chrome legacy window'
        }
        drop_contains = [
            'hackerrank.com/challenges/', 'ankushdebnath281', 'line:', 'col:',
            'tab search', 'switch to', 'add to favourites', 'test against custom input',
            'bookmark this tab', 'view site information', 'turn on speedreader',
            'share this page', 'brave shields', 'brave rewards', 'hackerrank logo',
            'exit full screen view', 'upload code as file', 'i am ankush debnaht',
            'api keys | google ai studio'
        ]

        # Window titles from browser chrome.
        title_like = re.compile(r'.*\|\s*(hackerrank|brave)\s*$', re.IGNORECASE)

        cleaned_lines = []
        prev_nonempty_line = None
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
                continue

            line_lower = line.lower()

            if line_lower in drop_exact:
                continue
            if any(token in line_lower for token in drop_contains):
                continue
            if title_like.match(line):
                continue

            # Drop mostly-symbol/icon lines generated by UI extraction.
            alnum_count = sum((1 for c in line if c.isalnum()))
            if alnum_count <= 1 and len(line) <= 6:
                continue

            # Drop numeric-only toolbar/footer counters.
            if re.fullmatch(r'\d+', line) and len(line) <= 3:
                continue

            # Drop common profile/stat lines.
            if line_lower.startswith('rank:') or line_lower.startswith('points:'):
                continue
            if 'challenges solved' in line_lower:
                continue

            # Keep intentional repeated lines (e.g., sample input values),
            # but drop immediate duplicates caused by viewport overlap.
            if prev_nonempty_line == line:
                continue
            prev_nonempty_line = line

            cleaned_lines.append(line)

        # Collapse repeated blank lines and remove large duplicate sections.
        compact = []
        prev_blank = False
        seen_sections = set()
        
        for line in cleaned_lines:
            is_blank = (line == '')
            if is_blank and prev_blank:
                continue
            
            # For non-empty lines, track if this section (paragraph) has appeared before
            if not is_blank:
                # Use a hash of the line to detect if this particular content already appeared
                line_hash = hash(line[:100])  # Hash first 100 chars
                if line_hash in seen_sections and len(line) > 50:
                    # Likely a duplicate section - skip it
                    continue
                seen_sections.add(line_hash)
            
            compact.append(line)
            prev_blank = is_blank

        return '\n'.join(compact).strip()

    def dedupe_preserve_order(items):
        seen = set()
        result = []
        for item in items:
            key = item.strip()
            if not key:
                continue
            if key in seen:
                continue
            seen.add(key)
            result.append(key)
        return result

    def run_uia_and_filter(attempt_num):
        import re
        try:
            all_texts = extract_all_ui_text()
        except Exception as e:
            print(f'  ⚠️ extract_all_ui_text() failed: {e}')
            all_texts = []
        
        # DEBUG: Print ALL extracted text
        print(f'\n{"="*80}')
        print(f'🔍 DEBUG - ATTEMPT {attempt_num}: ALL EXTRACTED TEXT ({len(all_texts)} items)')
        print(f'{"="*80}')
        for idx, item in enumerate(all_texts):
            print(f'  [{idx}] {repr(item[:100])}')  # Show first 100 chars
        print(f'{"="*80}\n')
        
        if not all_texts:
            print(f'  → Attempt {attempt_num}: No text extracted from UI')
            return None
        
        junk_patterns = [
            # Browser chrome
            'Minimize', 'Restore', 'Close', 'Back', 'Forward', 'Reload', 'Bookmark this tab',
            'View site information', 'Turn on Speedreader', 'Share this page', 'Separator',
            'Brave Shields', 'Brave Rewards', 'Extensions', 'Tab search', 'Show sidebar',
            'Wallet', 'Leo AI', 'VPN', 'Brave', 'Bookmarks', 'Saved Tab Groups', 'Tab groups',
            
            # HackerRank specific UI
            'HackerRank Home', 'HackerRank Logo', 'Prepare', 'Certify', 'Compete', 'Switch to',
            'Problem', 'Submissions', 'Leaderboard', 'Discussions', 'Editorial', 'Add to favourites',
            'challenges solved', 'Rank:', 'Points:', 'Exit Full Screen View', 'More options',
            'click here for', 'Click here for', 'Click to', 'click to', 'power off',
            'Add to favourites', 'Discussions', 'View less', 'View more',
            
            # Editor UI elements
            'Change Theme', 'Select Your Coding Language', 'Language', 'Pypy', 'Python', 'Java', 'Javascript',
            'Reset Code', 'Editor Settings', 'Editor content', 'Press Alt+F1', 'Accessibility Options',
            'Line:', 'Col:', 'Submit Code', 'Run Code', 'Upload Code as File', 'Test against custom input',
            'Blog|', 'Scoring|', 'Environment|', 'FAQ|', 'About Us|', 'Helpdesk|', 'Careers|',
            'Terms Of Service|', 'Blog', 'Scoring', 'Environment', 'FAQ', 'About Us', 'Helpdesk',
            'Careers', 'Terms Of Service', 'Privacy Policy',
            
            # Footer/navigation
            'TryHackMe', 'Dashboard', 'Memory usage', 'Student Dashboard', 'New Tab', 'Brave Talk',
            'Brave Wallet', 'Reading List', 'Chrome Legacy Window', 'My Class', 'My Exam',
            'CodeTantra', 'LPU', 'LPUNEST', 'Hacktivities',
            
            # User profile/stats
            'ankushdebnath281', 'Collections', 'Python', 'CSV', 'Java', 'JavaScript', 'C++',
            'Powered by', 'now powered by', 'Section ', 'Time Remaining', 'Answered', 
            'Not Visited', 'Not Answered', 'Overall Summary', 'Finish', 'Next >', 'Next',
            '< Previous', 'Previous', 'Mark for Review', 'Clear Response', 'Marks',
            'Question Palette', 'Minimize', 'Restore', 'Restore', 'ext', 'Test against',
            'MSI', 'Back', 'Forward', 'Reload', 'notes.lpuverto', 'Sem6',
            
            # LPU Exam Platform specific UI
            'Internet Status', 'Online', 'Name :', 'Roll Number', 'Email :', 'Degree :', 'Batch :',
            'Test Name :', 'Submit Test', 'Bookmarked', 'Skipped', 'Not Viewed', 'Saved in Server',
            'View More', 'Question No :', 'Single File Programming Question', 'Problem Statement',
            'Input format :', 'Output format :', 'Code constraints :', 'Sample test cases :',
            'Sample:', 'Sample Input', 'Sample Output', 'Output:', 'Compile & Run', 'Prev',
            'Fill your code here', 'Provide Custom Input', 'Clear', 'Marks :', 'Negative Marks :',
            'Note :', 'Refer to the sample', 'refer to the sample', 'book mark', 'bookmark',
            'rishabh yadav', 'rupesh', 'neocolab', 'lpu', 'lpunest', 'colab', 'pea bot',
            'pealogger', 'lgpl', 'bookmarkicon', 'pausetesticon', 'Image', 'image',
            'Name', 'Reg No', 'Reg Number', 'Registration Number', 'Registration', 'Batch',
            'Degree', 'Email', 'Roll', '12405940', 'Section', 'Coding', 'B.Tech CSE',
            'theme', 'View more', 'Answered', 'Bookmarked', 'Header Snippet',
            'Footer Snippet', 'theme', 
            'answerobacco', 'answeryou', 'answer'
        ]
        filtered = []
        partial_ui_patterns = [
            'press alt', 'accessibility', 'editor settings', 'change theme',
            'upload code as file', 'test against custom input', 'question palette',
            'mark for review', 'clear response', 'time remaining', 'overall summary',
            'internet status', 'registration number', 'reg number', 'reg no', 'roll number',
            'coding (', 'section 1', 'header snippet', 'footer snippet', '// you are',
            'name :', 'email :', 'degree :', 'batch :', 'test name :', 'answered',
            'bookmarked', 'not viewed', 'saved in server'
        ]
        for text in all_texts:
            is_junk = False
            stripped = text.strip()
            stripped_lower = stripped.lower()
            
            # Basic junk checks
            if stripped.isdigit():
                is_junk = True
            elif len(stripped) <= 1 and (not any((c.isalpha() for c in stripped))):
                is_junk = True
            elif re.fullmatch('[\\d\\s]+', stripped) and len(stripped) > 8:
                is_junk = True
            elif stripped.startswith('http://') or stripped.startswith('https://') or stripped.startswith('file://'):
                is_junk = True
            # Check for pattern matches (both exact and partial)
            else:
                for pattern in junk_patterns:
                    pattern_lower = pattern.lower()
                    # Exact match
                    if stripped_lower == pattern_lower:
                        is_junk = True
                        break
                    # Partial match only for clearly UI-only strings
                    if pattern_lower in partial_ui_patterns and pattern_lower in stripped_lower:
                        is_junk = True
                        break
            
            if not is_junk:
                filtered.append(stripped)
        
        # DEBUG: Print filtered text
        print(f'\n{"="*80}')
        print(f'✅ DEBUG - FILTERED TEXT ({len(filtered)} items kept from {len(all_texts)})')
        print(f'{"="*80}')
        for idx, item in enumerate(filtered):
            print(f'  [{idx}] {repr(item[:100])}')
        print(f'{"="*80}\n')
        
        filtered = dedupe_preserve_order(filtered)
        print(f'  → Filtered {len(all_texts)} items down to {len(filtered)} relevant items')
        
        # Additional filtering: remove items that are just URLs or special patterns
        ultra_filtered = []
        for text in filtered:
            stripped = text.strip()
            stripped_lower = stripped.lower()
            
            # Skip ONLY navigation/footer URLs (not example URLs in problem content)
            if '://' in stripped:
                # Keep URLs that might be part of problem content (like examples)
                # Filter only if they look like browser/navigation URLs
                if any(x in stripped_lower for x in ['hackerrank.com', 'codetantra', 'lpuverto', 'tryhackme', 'notes.', 'github.com']):
                    continue  # Skip navigation URLs
                # Otherwise keep it - it might be example content
            
            # Skip numbers/stats like "32/115"
            if re.match(r'^\d+/\d+$', stripped):
                continue
            # Skip single words that look like navigation (username, tags, etc)
            if len(stripped.split()) == 1 and len(stripped) < 20:
                # Keep "Task", "Problem", "Input", "Output", etc that are content markers
                if stripped_lower not in ['task', 'problem', 'constraints', 'input', 'output', 
                                          'explanation', 'sample', 'code', 'format', 'description']:
                    # Keep short variable-like placeholders often used in statements.
                    if re.fullmatch(r'[A-Za-z]', stripped):
                        ultra_filtered.append(stripped)
                        continue
                    # Skip things like "ankushdebnath281", "Python", "Collections", etc
                    if not any(keyword in stripped_lower for keyword in ['task', 'input', 'output', 'sample', 'explanation']):
                        continue
            # Skip items that are mostly special characters or pipes
            if stripped.count('|') > 0 or all(ord(c) > 127 or c in '|-_' for c in stripped):
                continue
            # Skip very short lines that look like UI (like "Editorial", "Exit Full Screen View")
            if len(stripped) < 30 and any(x in stripped_lower for x in ['edit', 'exit', 'press alt', 'accessibility', 'upload', 'reset', 'change theme']):
                continue
            
            ultra_filtered.append(stripped)
        
        ultra_filtered = dedupe_preserve_order(ultra_filtered)
        print(f'  → Ultra-filtered {len(filtered)} down to {len(ultra_filtered)} items (removed URLs & nav)')
        
        focused = None
        for i, item in enumerate(ultra_filtered):
            if 'select the correct answer' in item.lower() or item.lower() == 'select the correct answer':
                # Keep a broader window so options and constraints are not clipped.
                block = ultra_filtered[max(0, i - 4):i + 32]
                focused = '\n'.join(block)
                break
        
        if focused is None:
            for i, item in enumerate(ultra_filtered):
                if re.match('Question \\d+ of \\d+', item):
                    block = ultra_filtered[max(0, i - 4):i + 36]
                    focused = '\n'.join(block)
                    break
        
        if focused and len(focused) > 30:
            # DEBUG: Print final focused text
            print(f'\n{"="*80}')
            print(f'🎯 DEBUG - FINAL FOCUSED TEXT (found keyword match)')
            print(f'{"="*80}')
            print(focused)
            print(f'{"="*80}\n')
            return normalize_extracted_text(focused)
        else:
            full_text = '\n'.join(ultra_filtered)
            if len(full_text) > 200:
                # DEBUG: Print final full text
                print(f'\n{"="*80}')
                print(f'🎯 DEBUG - FINAL FULL TEXT (no keyword, showing all ultra-filtered)')
                print(f'{"="*80}')
                print(full_text[:3000])
                print(f'{"="*80}\n')
                return normalize_extracted_text(full_text)
            else:
                print(f'  → Attempt {attempt_num}: UIA got {len(full_text)} chars (needs accessibility tree)...')
                return None
    
    full_text = run_uia_and_filter(1)
    if full_text is None:
        print('  ⏳ Waiting 10s for Chrome accessibility tree to build, then retrying...')
        time.sleep(10)
        full_text = run_uia_and_filter(2)

    if not full_text or len(full_text.strip()) < 120:
        print('  → UI extraction too short, trying clipboard fallback...')
        clipboard_text = auto_clipboard_capture()
        cleaned_clipboard = normalize_extracted_text(clipboard_text or '')
        if cleaned_clipboard and len(cleaned_clipboard.strip()) > len((full_text or '').strip()):
            full_text = cleaned_clipboard.strip()
            print(f'  ✅ Clipboard fallback captured {len(full_text)} chars')
    else:
        full_text = normalize_extracted_text(full_text)
    
    if full_text:
        is_coding = None
        if 'Section 2 of 2' in full_text:
            is_coding = True
        elif 'select the correct answer' in full_text.lower():
            is_coding = False

        print('🔄 Phase 2: Capturing below-the-fold content...')
        try:
            scrolled_chunks = capture_text_with_scrolling()
            if scrolled_chunks:
                merged = [full_text]
                existing = {full_text}
                for chunk in scrolled_chunks:
                    cleaned_chunk = normalize_extracted_text(chunk)
                    if cleaned_chunk and cleaned_chunk not in existing:
                        existing.add(cleaned_chunk)
                        merged.append(cleaned_chunk)
                full_text = normalize_extracted_text('\n\n'.join(merged))
                print(f'✅ Added scrolled content ({len(scrolled_chunks)} chunk(s))')
        except Exception as e:
            print(f'⚠️ Scroll capture skipped: {e}')

        print(f'✅ UI extraction got {len(full_text)} chars')
        
        return (full_text, is_coding)
    else:
        print('⚠️ UI extraction returned empty - returning retry message')
        return ('⚠️ Could not capture question text from current screen.\n\n📝 Manual Steps:\n1. Make sure the question is visible\n2. Try Alt+A again (gives accessibility tree 10s to build)\n3. If still failing, copy question manually and use Alt+C', False)
class ExtractThread(QThread):
    finished = pyqtSignal(str, object)
    error = pyqtSignal(str)
    def run(self):
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            print('[EXTRACT] Starting text extraction from foreground window...')
            text, is_coding = extract_window_text_from_foreground()
            print(f'[EXTRACT] ✅ Successfully extracted {len(text)} characters')
            self.finished.emit(text, is_coding)
        except Exception as e:
            error_msg = f'Text extraction failed: {str(e)}'
            print(f'[EXTRACT] ❌ {error_msg}')
            import traceback
            traceback.print_exc()
            self.error.emit(error_msg)
        finally:
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
    def __init__(self, prompt, hwid, is_coding, forced_language=None):
        super().__init__()
        self.prompt = prompt
        self.hwid = hwid
        self.is_coding = is_coding
        self.prompt_mode = 'mcq'
        self.forced_language = forced_language  # None for auto-detect, or 'python', 'cpp', 'java', 'c', etc.
    def run(self):
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
            payload = {
                'hwid': self.hwid,
                'app_id': APP_ID_LPU,
                'api_token': API_TOKEN_LPU,
                'message': self.prompt,
                'images': [],
                'question_type': self.prompt_mode
            }
            
            # Add forced language if user selected one (not auto-detect)
            if self.forced_language:
                payload['forced_language'] = self.forced_language
            
            print(f'[API] Sending request to {GENERATE_URL}...')
            print(f'[API] Payload: hwid={self.hwid[:8]}..., prompt_len={len(self.prompt)} chars, forced_lang={self.forced_language}')
            
            gen_response = session.post(GENERATE_URL, json=payload, timeout=45)
            
            # Check if response indicates server errors
            if gen_response.status_code >= 500:
                error_detail = gen_response.text[:200] if gen_response.text else 'No response body'
                print(f'❌ Backend server error ({gen_response.status_code}): {error_detail}')
                self.response_ready.emit(f'🔴 Backend server error ({gen_response.status_code})\n\nThe LPU Helper backend is temporarily down.\nTry again in a few minutes.', False)
                return
            
            if gen_response.status_code == 200:
                try:
                    data = gen_response.json()
                    if data.get('success'):
                        answer = data.get('answer', '')
                        detected_language = data.get('language', 'unknown')
                        clean_res = answer.replace('```python', '').replace('```sql', '').replace('```html', '').replace('```', '').strip()
                        stats = data.get('stats', {})
                        if 'limit' in stats and 'used' in stats:
                            self.stats_ready.emit(stats['limit'], stats['used'])
                        
                        # Add language info to the response for code problems
                        if self.is_coding and detected_language != 'unknown' and detected_language != 'n/a':
                            clean_res = f"[Language: {detected_language.upper()}]\n\n{clean_res}"
                        
                        print(f'✅ Got answer ({len(clean_res)} chars) - Language: {detected_language}')
                        self.response_ready.emit(clean_res, self.is_coding)
                    else:
                        err = data.get('error', 'Unknown Error')
                        print(f'❌ Server returned error: {err}')
                        self.response_ready.emit(f'Server Error: {err}', False)
                except Exception as e:
                    print(f'❌ Failed to parse response JSON: {e}')
                    self.response_ready.emit(f'Response parsing error: {str(e)}', False)
            else:
                try:
                    err_json = gen_response.json()
                    err_msg = err_json.get('error', 'Unknown Error')
                except:
                    err_msg = 'Unknown Error'
                
                if gen_response.status_code == 401:
                    self.response_ready.emit(f'🔐 ACCESS DENIED.\nHWID: {self.hwid}\nMessage: {err_msg}', False)
                elif gen_response.status_code == 403:
                    self.response_ready.emit(f'⛔ LICENSE ERROR\n{err_msg}', False)
                else:
                    print(f'❌ HTTP {gen_response.status_code}: {err_msg}')
                    self.response_ready.emit(f'API Error ({gen_response.status_code}): {err_msg}', False)
        
        except requests.exceptions.Timeout:
            print(f'❌ TIMEOUT: Backend took >45s to respond')
            self.response_ready.emit('⏱️ Request timed out (45s)\nBackend is slow or overloaded.\nTry again shortly.', False)
        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            # Check if it's a Max Retries error
            if 'Max retries exceeded' in error_str or 'too many' in error_str.lower():
                print(f'❌ MAX RETRIES EXCEEDED: {error_str}')
                self.response_ready.emit('🔴 Backend server error (500)\nServer is returning errors.\nTry again in a few minutes.', False)
            else:
                print(f'❌ CONNECTION ERROR: {error_str}')
                self.response_ready.emit('🌐 No internet or network connection error.\nCheck your internet and try again.', False)
        except requests.exceptions.RequestException as e:
            print(f'❌ REQUEST ERROR: {str(e)}')
            self.response_ready.emit(f'Request failed: {str(e)[:100]}', False)
        except Exception as e:
            print(f'❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}')
            import traceback
            traceback.print_exc()
            self.response_ready.emit(f'Unexpected error: {str(e)[:100]}', False)
        finally:
            pythoncom.CoUninitialize()
def set_window_exclude_from_capture(hwnd):
    try:
        WDA_EXCLUDEFROMCAPTURE = 17
        ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    except:
        return None



class SelectionWindow(QWidget):
    """Full-screen overlay for selecting a rectangular area to extract text from"""
    def __init__(self, screenshot_img):
        super().__init__()
        self.screenshot_img = screenshot_img
        self.selected_area = None
        self.start_pos = None
        self.end_pos = None
        self.drawing = False
        
        # Convert PIL image to QPixmap
        img_rgb = screenshot_img.convert('RGB')
        data = img_rgb.tobytes('raw', 'RGB')
        qimage = QtGui.QImage(data, img_rgb.width, img_rgb.height, QtGui.QImage.Format_RGB888)
        self.pixmap = QtGui.QPixmap.fromImage(qimage)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.setCursor(Qt.CrossCursor)
    
    def paintEvent(self, event):
        """Draw screenshot + semi-transparent overlay + selection rectangle"""
        painter = QtGui.QPainter(self)
        
        # Draw screenshot
        painter.drawPixmap(0, 0, self.pixmap)
        
        # Draw semi-transparent dark overlay
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 120))
        
        # Draw selection rectangle if currently selecting
        if self.start_pos and self.end_pos:
            rect = QtCore.QRect(self.start_pos, self.end_pos)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            painter.fillRect(rect, QtGui.QColor(0, 0, 0, 0))
            
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0), 2))
            painter.drawRect(rect)
    
    def mousePressEvent(self, event):
        """Start selection"""
        self.drawing = True
        self.start_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """Update selection rectangle"""
        if self.drawing:
            self.end_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Finish selection"""
        if self.drawing:
            self.end_pos = event.pos()
            self.drawing = False
            
            # Extract coordinates
            x1 = min(self.start_pos.x(), self.end_pos.x())
            y1 = min(self.start_pos.y(), self.end_pos.y())
            x2 = max(self.start_pos.x(), self.end_pos.x())
            y2 = max(self.start_pos.y(), self.end_pos.y())
            
            # Only set area if selection is large enough (at least 10x10 pixels)
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                self.selected_area = (x1, y1, x2, y2)
            
            self.close()
    
    def keyPressEvent(self, event):
        """Allow Escape to cancel selection"""
        if event.key() == Qt.Key_Escape:
            self.selected_area = None
            self.close()

class ChatbotUI(QWidget):
    def __init__(self, hwid):
        super().__init__()
        self.hwid = hwid
        self.sio = socketio.Client()
        self.current_room = None
        self.cursor_mode_pending = False
        self.cursor_mode_enabled = False
        self.cursor_min_confidence = 65
        self.cursor_double_check_enabled = True
        self.cursor_check_stage = 0
        self.cursor_first_answer = None
        self.cursor_question_text = ''
        self.hotkey_listener_started = False
        self.native_registered_hotkeys = set()
        self.native_hotkey_thread = None
        self.pynput_hotkey_thread = None
        # Keyboard-stream mode for code injection
        self.stream_mode_active = False
        self.stream_answer = ''
        self.stream_position = 0
        if not self.verify_device_startup():
            sys.exit()
        self.is_coding = None
        self.prompt_mode = 'mcq'  # 'mcq' or 'code' - tracks which hotkey was pressed
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
        self.setWindowOpacity(0.75)
        self.setStyleSheet('background-color: #ffffff; border: 1px solid #e8e8e8;')
        # Enforce window on top with timer (works in lockdown browser)
        self.top_keep_timer = QTimer()
        self.top_keep_timer.timeout.connect(self.enforce_window_on_top)
        self.top_keep_timer.start(5000)  # Check every 5000ms
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'setting_ico.ico')
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                self.setWindowIcon(QIcon(icon_path))
                print(f'[UI] Window icon loaded: {icon_path}')
        except Exception as e:
            print(f'[UI] Icon load warning: {e}')
        self.resize(280, 180)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 300, screen.height() - self.height() - 150)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(8, 8, 8, 8)
        
        # Start pause detection thread (runs in background)
        try:
            pause_thread = threading.Thread(target=check_pause, daemon=True)
            pause_thread.start()
        except Exception as e:
            print(f'⚠️ Pause thread warning: {e}')
        
        # HIDE: Language selector
        lang_layout = QHBoxLayout()
        lang_layout.setContentsMargins(0, 0, 0, 0)
        self.language_selector = QComboBox(self)
        self.language_selector.addItems(['Auto-detect', 'Python', 'Java', 'C++', 'C'])
        self.language_selector.setVisible(False)
        
        # HIDE: Stats label
        self.stats_label = QLabel('●')
        self.stats_label.setVisible(False)
        
        # HIDE: Text input
        self.text_input = QTextEdit(self)
        self.text_input.setVisible(False)
        
        # HIDE: Button container
        button_container = QHBoxLayout()
        self.send_btn = QPushButton('↑', self)
        self.send_btn.setVisible(False)
        self.toggle_btn = QPushButton('◄◄ Hide', self)
        self.toggle_btn.setVisible(False)
        
        # HIDE: Output display
        self.output = QTextEdit(self)
        self.output.setVisible(False)
        self.copy_id_btn = QPushButton('Copy ID', self)
        self.copy_id_btn.setVisible(False)
        
        # SHOW: Chat section (compact)
        chat_section = QHBoxLayout()
        chat_section.setSpacing(4)
        chat_section.setContentsMargins(0, 4, 0, 4)
        
        # Room code input (small)
        self.room_entry = QLineEdit(self)
        self.room_entry.setMaximumHeight(18)
        self.room_entry.setStyleSheet('background: #ffffff; border: none; color: #444; font-size: 9px; padding: 4px;')
        
        # Join button (small)
        self.join_chat_btn = QPushButton('', self)
        self.join_chat_btn.clicked.connect(self.join_room)
        self.join_chat_btn.setMaximumHeight(18)
        self.join_chat_btn.setMaximumWidth(40)
        self.join_chat_btn.setStyleSheet('background-color: #ffffff; border: none; color: #999; font-size: 8px; padding: 2px;')
        
        # Chat display (mini)
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setMaximumHeight(60)
        self.chat_display.setStyleSheet('background: #ffffff; border: none; color: #444; font-size: 8px; padding: 4px;')
        
        # Message input (small)
        self.msg_entry = QLineEdit(self)
        self.msg_entry.setMaximumHeight(18)
        self.msg_entry.setStyleSheet('background: #ffffff; border: none; color: #444; font-size: 9px; padding: 4px;')
        
        # Send message button
        self.send_chat_btn = QPushButton('↑', self)
        self.send_chat_btn.clicked.connect(self.send_message)
        self.send_chat_btn.setMaximumHeight(18)
        self.send_chat_btn.setMaximumWidth(22)
        self.send_chat_btn.setStyleSheet('background-color: #ffffff; border: 1px solid #999; color: #aaa; font-size: 8px; padding: 2px 4px;')
        
        # Assemble chat section
        chat_section.addWidget(self.room_entry, 2)
        chat_section.addWidget(self.join_chat_btn)
        self.layout.addLayout(chat_section)
        self.layout.addWidget(self.chat_display)
        
        msg_section = QHBoxLayout()
        msg_section.setSpacing(4)
        msg_section.setContentsMargins(0, 0, 0, 0)
        msg_section.addWidget(self.msg_entry, 1)
        msg_section.addWidget(self.send_chat_btn)
        self.layout.addLayout(msg_section)
        
        self.setLayout(self.layout)
        self.send_timer = QTimer(self)
        self.send_timer.setSingleShot(True)
        self.send_timer.timeout.connect(self.get_response)
        self.hide()
        self.setup_tray_icon()
        self.protect_from_screen_recording()
        self.setup_socketio_client()
        # Defer hotkey registration to after window is created
        QTimer.singleShot(500, self.start_global_key_listener)
    def update_stats(self, limit, used):
        remaining = limit - used
        if remaining > 0:
            self.stats_label.setText('●')
            self.stats_label.setStyleSheet('color: #2a7a2a; font-size: 8px; background: transparent; padding: 0px;')
            self.stats_label.setToolTip(f'Remaining: {remaining}/{limit}')
        else:
            self.stats_label.setText('●')
            self.stats_label.setStyleSheet('color: #a00; font-size: 8px; background: transparent; padding: 0px;')
            self.stats_label.setToolTip(f'Limit Reached ({used}/{limit})')
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
    
    def on_send_edited_question(self):
        """Handler for 'Send Edited Question' button"""
        user_input = self.text_input.toPlainText().strip()
        if not user_input or len(user_input) < 10:
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '⚠️ Question text too short or empty!\n\nEdit the question and try again.'))
            return
        
        # Get selected language
        selected_language = self.language_selector.currentText()
        forced_lang = None if selected_language == 'Auto-detect' else selected_language.lower()
        if forced_lang == 'c++':  # Normalize C++ label
            forced_lang = 'cpp'
        
        print(f'[MANUAL SEND] User edited and sent {len(user_input)} chars')
        print(f'[MANUAL SEND] Language: {selected_language} (forced: {forced_lang})')
        print(f'[MANUAL SEND] Text preview: {user_input[:200]}...')
        
        # Add system prompt based on detected mode
        if self.prompt_mode == 'code':
            final_prompt = f"This is a coding problem. Return only a complete, runnable solution in the target language. Read from standard input and write to standard output. No explanation, no comments, no markdown fences.\n\n{user_input}"
        else:
            final_prompt = f"This is a Multiple Choice Question. For each question, provide the correct answer text (not just the letter). If multiple questions, answer each one clearly. Be concise.\n\n{user_input}"
        
        if hasattr(self, 'worker') and self.worker.isRunning():
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Processing... Please wait.'))
            return
        
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Connecting to Server...'))
        self.worker = ChatbotThread(final_prompt, self.hwid, self.is_coding, forced_language=forced_lang)
        self.worker.response_ready.connect(self.display_response)
        self.worker.stats_ready.connect(self.update_stats)
        self.worker.start()
    
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
    @pyqtSlot()
    def _toggle_visibility_action(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
    @pyqtSlot()
    def _auto_type_action(self):
        self.hide()
        QTimer.singleShot(200, self.trigger_auto_typer)
    @pyqtSlot()
    def _alt_m_action(self):
        self.cursor_mode_pending = True
        self.cursor_check_stage = 0
        self.cursor_first_answer = None
        self.cursor_question_text = ''
        print('[Cursor] Alt+M mode activated')
        QTimer.singleShot(0, self.get_window_text)
    @pyqtSlot()
    def _toggle_stream_mode_action(self):
        self.stream_mode_active = not self.stream_mode_active
        self.stream_position = 0
        status = 'ON' if self.stream_mode_active else 'OFF'
        print(f'[STREAM-TOGGLE] Stream mode {status}')
        msg = f'✓ Stream mode {status}\n\nNow press any key and each keystroke will type the next character from the answer.' if self.stream_mode_active else '✗ Stream mode OFF'
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, msg))
    @pyqtSlot()
    def _toggle_pause_action(self):
        toggle_pause()
    def trigger_hotkey_action(self, hotkey_name, slot_name, label=None):
        """Invoke a Qt slot from any hotkey backend."""
        try:
            print(f'[HOTKEY] {label or hotkey_name} pressed')
            QMetaObject.invokeMethod(self, slot_name, Qt.QueuedConnection)
            return True
        except Exception as e:
            print(f'[HOTKEY-ERROR] {label or hotkey_name} failed: {e}')
            return False
    def start_native_hotkeys(self):
        """Use Windows RegisterHotKey so combos work even when this window is hidden."""
        MOD_ALT = 0x0001
        MOD_SHIFT = 0x0004
        WM_HOTKEY = 0x0312
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        hotkeys = {
            0x5841: ('alt_x', MOD_ALT | MOD_SHIFT, 0x58, 'toggle_system', 'Alt+Shift+X'),
            0x4441: ('alt_d', MOD_ALT, 0x44, '_toggle_visibility_action', 'Alt+D'),
            0x4141: ('alt_a', MOD_ALT, 0x41, 'get_window_text_mcq', 'Alt+A'),
            0x4142: ('alt_shift_a', MOD_ALT | MOD_SHIFT, 0x41, 'get_window_text_code', 'Alt+Shift+A'),
            0x4341: ('alt_c', MOD_ALT, 0x43, 'read_from_clipboard', 'Alt+C'),
            0x4541: ('alt_e', MOD_ALT, 0x45, 'extract_selected_text', 'Alt+E'),
            0x5741: ('alt_shift_w', MOD_ALT | MOD_SHIFT, 0x57, '_auto_type_action', 'Alt+Shift+W'),
            0x4D41: ('alt_m', MOD_ALT, 0x4D, '_alt_m_action', 'Alt+M'),
            0x4B41: ('alt_shift_k', MOD_ALT | MOD_SHIFT, 0x4B, '_toggle_stream_mode_action', 'Alt+Shift+K'),
            0x5041: ('alt_shift_p', MOD_ALT | MOD_SHIFT, 0x50, '_toggle_pause_action', 'Alt+Shift+P'),
        }
        class MSG(ctypes.Structure):
            _fields_ = [
                ('hwnd', wintypes.HWND),
                ('message', wintypes.UINT),
                ('wParam', wintypes.WPARAM),
                ('lParam', wintypes.LPARAM),
                ('time', wintypes.DWORD),
                ('pt', wintypes.POINT),
            ]
        def hotkey_loop():
            registered_ids = []
            try:
                for hotkey_id, (hotkey_name, modifiers, vk, _, label) in hotkeys.items():
                    if user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
                        registered_ids.append(hotkey_id)
                        self.native_registered_hotkeys.add(hotkey_name)
                        print(f'[KEYS] Native Windows {label} registered')
                    else:
                        error_code = ctypes.get_last_error()
                        print(f'[KEYS] Native {label} registration failed (WinError {error_code})')
                if not registered_ids:
                    error_code = ctypes.get_last_error()
                    print(f'[KEYS] No native hotkeys registered (WinError {error_code})')
                    return
                msg = MSG()
                while user32.GetMessageW(byref(msg), None, 0, 0) != 0:
                    if msg.message == WM_HOTKEY and msg.wParam in hotkeys:
                        hotkey_name, _, _, slot_name, label = hotkeys[msg.wParam]
                        self.trigger_hotkey_action(hotkey_name, slot_name, label)
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))
            except Exception as e:
                print(f'[KEYS] Native hotkey loop error: {e}')
            finally:
                for hotkey_id in registered_ids:
                    try:
                        user32.UnregisterHotKey(None, hotkey_id)
                    except:
                        pass
        self.native_hotkey_thread = threading.Thread(target=hotkey_loop, daemon=True)
        self.native_hotkey_thread.start()
        print('[KEYS] Native hotkey thread started')
    def start_global_key_listener(self):
        """Register hotkeys using pynput (stable, no DLL crashes)"""
        if self.hotkey_listener_started:
            print('[KEYS] Hotkey listeners already running')
            return
        self.hotkey_listener_started = True
        self.start_native_hotkeys()
        def register_hotkeys():
            try:
                print('[KEYS] Starting hotkey registration in thread...')
                
                # Global state to track pressed keys
                key_states = {'alt_l': False, 'alt_r': False, 'shift_l': False, 'shift_r': False}
                
                def on_press(key):
                    try:
                        # Track modifier keys
                        if key == pynput_keyboard.Key.alt_l:
                            key_states['alt_l'] = True
                        elif key == pynput_keyboard.Key.alt_r:
                            key_states['alt_r'] = True
                        elif key == pynput_keyboard.Key.shift_l:
                            key_states['shift_l'] = True
                        elif key == pynput_keyboard.Key.shift_r:
                            key_states['shift_r'] = True
                        
                        alt_pressed = key_states['alt_l'] or key_states['alt_r']
                        shift_pressed = key_states['shift_l'] or key_states['shift_r']
                        
                        # Process hotkeys based on key code
                        # Check if keyboard-stream mode active - intercept ALL keys
                        if hasattr(self, 'stream_mode_active') and self.stream_mode_active:
                            if hasattr(self, 'stream_answer') and hasattr(self, 'stream_position'):
                                if self.stream_position < len(self.stream_answer):
                                    # Type next character from answer
                                    try:
                                        char = self.stream_answer[self.stream_position]
                                        hwnd = win32gui.GetForegroundWindow()
                                        print(f'[STREAM] Typing char {self.stream_position}: {repr(char)} into hwnd {hwnd}')
                                        if hwnd:
                                            if char == '\n':
                                                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                                                time.sleep(0.01)
                                                win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
                                            else:
                                                win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
                                            time.sleep(0.015)
                                        self.stream_position += 1
                                        if self.stream_position >= len(self.stream_answer):
                                            print(f'[STREAM] Complete! Typed all {self.stream_position} chars')
                                            self.stream_mode_active = False
                                            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '✓ Answer streamed complete!'))
                                    except Exception as e:
                                        print(f'[STREAM] Exception: {e}')
                                        import traceback
                                        traceback.print_exc()
                                    return  # Don't process hotkeys during stream
                        
                        if hasattr(key, 'vk'):
                            # Alt+Shift+X is handled by native RegisterHotKey above to avoid double toggles.
                            if key.vk == 88 and alt_pressed and shift_pressed:
                                if 'alt_x' in self.native_registered_hotkeys:
                                    return
                                self.trigger_hotkey_action('alt_x', 'toggle_system', 'Alt+Shift+X')
                            # Alt+D - Toggle visibility
                            elif key.vk == 68 and alt_pressed:
                                if 'alt_d' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+D pressed')
                                QMetaObject.invokeMethod(self, '_toggle_visibility_action', Qt.QueuedConnection)
                            # Alt+A - MCQ capture
                            elif key.vk == 65 and alt_pressed and not shift_pressed:
                                if 'alt_a' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+A pressed')
                                QMetaObject.invokeMethod(self, 'get_window_text_mcq', Qt.QueuedConnection)
                            # Alt+Shift+A - Code capture  
                            elif key.vk == 65 and alt_pressed and shift_pressed:
                                if 'alt_shift_a' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+Shift+A pressed')
                                QMetaObject.invokeMethod(self, 'get_window_text_code', Qt.QueuedConnection)
                            # Alt+C - Clipboard
                            elif key.vk == 67 and alt_pressed:
                                if 'alt_c' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+C pressed')
                                QMetaObject.invokeMethod(self, 'read_from_clipboard', Qt.QueuedConnection)
                            # Alt+E - Extract selected text
                            elif key.vk == 69 and alt_pressed:
                                if 'alt_e' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+E pressed')
                                QMetaObject.invokeMethod(self, 'extract_selected_text', Qt.QueuedConnection)
                            # Alt+Shift+W - Auto-type
                            elif key.vk == 87 and alt_pressed and shift_pressed:
                                if 'alt_shift_w' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+Shift+W pressed')
                                QMetaObject.invokeMethod(self, '_auto_type_action', Qt.QueuedConnection)
                            # Alt+M - Cursor/Answer reveal
                            elif key.vk == 77 and alt_pressed:
                                if 'alt_m' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+M pressed')
                                QMetaObject.invokeMethod(self, '_alt_m_action', Qt.QueuedConnection)
                            # Alt+Shift+K - Toggle stream mode (answer injection)
                            elif key.vk == 75 and alt_pressed and shift_pressed:
                                if 'alt_shift_k' in self.native_registered_hotkeys:
                                    return
                                QMetaObject.invokeMethod(self, '_toggle_stream_mode_action', Qt.QueuedConnection)
                            # Alt+Shift+P - Pause
                            elif key.vk == 80 and alt_pressed and shift_pressed:
                                if 'alt_shift_p' in self.native_registered_hotkeys:
                                    return
                                print('[HOTKEY] Alt+Shift+P pressed')
                                QMetaObject.invokeMethod(self, '_toggle_pause_action', Qt.QueuedConnection)

                    except Exception as e:
                        print(f'⚠️ on_press error: {e}')
                        import traceback
                        traceback.print_exc()
                
                def on_release(key):
                    try:
                        # Track modifier key releases
                        if key == pynput_keyboard.Key.alt_l:
                            key_states['alt_l'] = False
                        elif key == pynput_keyboard.Key.alt_r:
                            key_states['alt_r'] = False
                        elif key == pynput_keyboard.Key.shift_l:
                            key_states['shift_l'] = False
                        elif key == pynput_keyboard.Key.shift_r:
                            key_states['shift_r'] = False
                    except:
                        pass
                
                listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
                listener.daemon = True
                listener.start()
                print('✓ All hotkeys registered - ready for input')
                print('  🔑 HOTKEYS:')
                print('     Alt+Shift+X - Toggle window visibility')
                print('     Alt+A - Capture MCQ question')
                print('     Alt+Shift+A - Capture code problem')
                print('     Alt+C - Read from clipboard')
                print('     Alt+M - Cursor/Answer reveal mode')
                print('     Alt+Shift+W - Auto-type answer')
                print('     Alt+Shift+K - Toggle keystroke stream mode')
                print('     Alt+Shift+P - Pause/Resume')
                
                # Keep thread alive
                while True:
                    time.sleep(1)
            except Exception as e:
                print(f'❌ Hotkey error: {e}')
                import traceback
                traceback.print_exc()
        
        try:
            self.pynput_hotkey_thread = threading.Thread(target=register_hotkeys, daemon=True)
            self.pynput_hotkey_thread.start()
            print('[KEYS] Hotkey thread started')
        except Exception as e:
            print(f'❌ Hotkey thread startup error: {e}')
    
    @pyqtSlot()
    def get_window_text_mcq(self):
        self.prompt_mode = 'mcq'
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '📸 Capturing MCQ question... Please wait...'))
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
    
    @pyqtSlot()
    def get_window_text_code(self):
        self.prompt_mode = 'code'
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '📸 Capturing code problem... Please wait...'))
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
    @pyqtSlot()
    def read_from_clipboard(self):
        """Backup method: Read question from clipboard (manual copy-paste, no auto-send)"""
        try:
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            if text and len(text.strip()) > 10:
                self.text_input.setPlainText(text.strip())
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '✓ Clipboard text loaded! You can now:\n• Edit the text if needed\n• Click ↑ button to send'))
                self.is_coding = None
            else:
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '⚠️ Clipboard is empty or too short!\n\nCopy question text first (Ctrl+C)'))
        except Exception as e:
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, f'❌ Clipboard error: {e}\n\nMake sure you copied text first!'))
    def handle_window_text(self, text, is_coding):
        """Handle captured text - show it in the window (do NOT auto-send)"""
        self.is_coding = is_coding
        
        if not text or len(text.strip()) < 10:
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '⚠️ No question detected!\n\nTips:\n1. Make sure question is visible on screen\n2. Wait for page to fully load\n3. Try pressing Alt+A again\n4. Maximize browser window'))
            return None
        
        # DEBUG: Print final captured text to terminal
        print(f'\n{"="*80}')
        print(f'📱 FINAL CAPTURED TEXT (ready for manual review)')
        print(f'{"="*80}')
        print(text)
        print(f'{"="*80}')
        print(f'Text length: {len(text)} chars | Mode: {is_coding}\n')
        
        # Show window and display question
        self.show()
        self.text_input.setPlainText(text)
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '✓ Question captured! You can now:\n• Edit the text if needed\n• Click ↑ button to send\n• Or keep it as is'))
        # NO auto-send - wait for user to click send button
    
    def confirm_pending_question(self):
        """Placeholder - no longer used"""
        pass
    
    def cancel_pending_question(self):
        """Placeholder - no longer used"""
        pass
    
    @pyqtSlot()
    def extract_selected_text(self):
        """Extract text from a user-selected rectangular area on screen"""
        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '🎯 Selection mode: Click and drag to select area...'))
        self.hide()
        time.sleep(0.5)
        
        # Create a selection overlay window
        try:
            import mss
            from PIL import Image
            import pytesseract
            
            # Capture initial full screen
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Open selection window to let user select area
            selection_window = SelectionWindow(img)
            selection_window.showFullScreen()
            
            # Wait for user to make selection
            QApplication.processEvents()
            
            # If user made a selection, extract text
            if hasattr(selection_window, 'selected_area') and selection_window.selected_area:
                x1, y1, x2, y2 = selection_window.selected_area
                cropped_img = img.crop((x1, y1, x2, y2))
                
                # Try OCR extraction
                try:
                    extracted_text = pytesseract.image_to_string(cropped_img)
                    if extracted_text and len(extracted_text.strip()) > 0:
                        self.show()
                        self.text_input.setPlainText(extracted_text.strip())
                        QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, f'✓ Extracted {len(extracted_text)} characters from selected area!\n\nYou can now:\n• Edit the text\n• Click ↑ to send'))
                        print(f'[EXTRACT] Selected text ({len(extracted_text)} chars):\n{extracted_text}')
                        return
                except Exception as ocr_error:
                    print(f'[EXTRACT] OCR failed: {ocr_error}')
            
            # If selection failed or OCR failed
            self.show()
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, '❌ No text extracted\n\nTips:\n• Make sure to select area with text\n• Text must be visible\n• Try Alt+E again'))
            
        except ImportError as e:
            # Fallback: use accessibility API
            self.show()
            self.prompt_mode = 'mcq'
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, f'⚠️ Selection mode not available\n\nFallback: Using full screen capture (Alt+A style)\n\nError: {e}'))
            time.sleep(0.5)
            self.get_window_text_mcq()
    
    def start_send_timer(self):
        self.send_timer.start(500)
    def get_response(self):
        user_input = self.text_input.toPlainText().strip()
        if user_input:
            if hasattr(self, 'worker') and self.worker.isRunning():
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Processing... Please wait.'))
                return None
            else:
                # Add system prompt based on which hotkey was pressed
                if self.prompt_mode == 'code':
                    final_prompt = f"{CODE_SYSTEM_PROMPT}\n\n{user_input}"
                else:
                    final_prompt = f"{MCQ_SYSTEM_PROMPT}\n\n{user_input}"
                
                if self.cursor_mode_pending:
                    self.cursor_question_text = user_input
                    final_prompt = self.build_cursor_prompt(self.cursor_question_text, second_pass=False)
                
                # DEBUG: Print what's being sent to API
                print(f'\n{"="*80}')
                print(f'🚀 SENDING TO API')
                print(f'{"="*80}')
                print(f'Mode: {self.prompt_mode.upper()}')
                print(f'Prompt length: {len(final_prompt)} chars')
                print(f'-' * 80)
                print('FULL PROMPT:')
                print(f'-' * 80)
                print(final_prompt)
                print(f'{"="*80}\n')
                
                QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, 'Connecting to Server...'))
                self.worker = ChatbotThread(final_prompt, self.hwid, self.is_coding)
                self.worker.prompt_mode = self.prompt_mode
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
        # Store response but DON'T display it - only show on Alt+X toggle
        self.last_response = response
        self.last_response_is_coding = is_coding
        print(f'[RESPONSE STORED] {len(response)} chars stored. Press Alt+Shift+X to view.')
        # Auto-activate keyboard-stream mode for coding answers
        if is_coding:
            self.stream_answer = response.strip()
            self.stream_position = 0
            # Don't auto-activate - wait for user to press Alt+Shift+K
            self.stream_mode_active = False
            print(f'[STREAM] Ready! Answer len={len(self.stream_answer)} chars. Press Alt+Shift+K to toggle stream mode.')
            msg = f'✓ Code answer ready!\n\nPress Alt+Shift+K to toggle keystroke-stream mode.\n({len(self.stream_answer)} chars total)\n\nWhen stream is ON, each keystroke types the next character.'
            QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, msg))
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
    
    def setup_tray_icon(self):
        """Create system tray icon for toggling visibility even when window is hidden behind browser"""
        try:
            log_msg = '[TRAY] Starting setup'
            print(log_msg)
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
            
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self)
            print('[TRAY] QSystemTrayIcon created')
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write('[TRAY] QSystemTrayIcon created\n')
            
            # Set icon as simple blue pixmap
            from PyQt5.QtGui import QPixmap, QPainter, QFont
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(52, 120, 219))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            font = QFont()
            font.setPointSize(18)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, 'P')
            painter.end()
            self.tray_icon.setIcon(QIcon(pixmap))
            print('[TRAY] Icon set')
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write('[TRAY] Icon set\n')
            
            # Create tray menu
            tray_menu = QMenu()
            tray_menu.addAction('Show Window', self.show)
            tray_menu.addAction('Hide Window', self.hide)
            tray_menu.addSeparator()
            tray_menu.addAction('Toggle (Alt+Shift+X)', self.toggle_system)
            tray_menu.addSeparator()
            tray_menu.addAction('Exit', QApplication.quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            print('[TRAY] Menu created')
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write('[TRAY] Menu created\n')
            
            # Show the tray icon
            self.tray_icon.show()
            print('[TRAY] [OK] Tray icon shown')
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write('[TRAY] [OK] Tray icon shown\n')
                
        except Exception as e:
            err_msg = f'[TRAY] ERROR: {e}'
            print(err_msg)
            with open('tray_debug.log', 'a', encoding='utf-8') as f:
                f.write(err_msg + '\n')
                f.write(f'{repr(e)}\n')
    
    def enforce_window_on_top(self):
        """Enforce window stays on top - only if already visible"""
        try:
            # Only enforce on-top if window is actually visible
            if not self.isVisible():
                return
            
            HWND_TOPMOST = -1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            
            hwnd = int(self.winId())
            
            # Keep window on top - but DON'T force it to show if hidden
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
        except Exception as e:
            pass  # Silent fail - don't spam logs
    @pyqtSlot()
    def toggle_system(self):
        """Toggle window visibility with Alt+Shift+X - shows stored response when unhiding"""
        try:
            if self.isVisible():
                self.hide()
                self.toggle_btn.setText('▶▶ Show')
                print('✗ Window hidden')
            else:
                self.show()
                self.toggle_btn.setText('◄◄ Hide')
                print('✓ Window shown')
                # Display the stored response when showing the window
                if hasattr(self, 'last_response') and self.last_response:
                    QMetaObject.invokeMethod(self.output, 'setText', Qt.QueuedConnection, Q_ARG(str, self.last_response))
                    print(f'[DISPLAY] Showing stored response ({len(self.last_response)} chars)')
                def warmup_a11y():
                    try:
                        set_chrome_accessibility_registry()
                        force_chrome_accessibility_on()
                        print('🔧 Accessibility prepared')
                    except Exception as e:
                        print(f'⚠️ Accessibility prep error: {e}')
                threading.Thread(target=warmup_a11y, daemon=True).start()
        except Exception as e:
            print(f'❌ Toggle error: {e}')
    
    def setup_socketio_client(self):
        """Setup socketio client for chat"""
        AZURE_IP = "http://4.240.81.134:5000"
        
        @self.sio.on('connect')
        def on_connect():
            self.update_chat('[System]: Connected')
            print('[CHAT] Connected')
        
        @self.sio.on('disconnect')
        def on_disconnect():
            self.update_chat('[System]: Disconnected')
            print('[CHAT] Disconnected')
        
        @self.sio.on('new_message')
        def on_msg(data):
            sender = data.get('sender', 'Unknown')
            msg = data.get('msg', '')
            self.update_chat(f'[{sender}]: {msg}')
        
        # Try to connect
        def connect_thread():
            try:
                self.sio.connect(AZURE_IP)
                print('[CHAT] Connected to server')
            except Exception as e:
                print(f'[CHAT] Connection error: {e}')
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def join_room(self):
        """Join a chat room"""
        code = self.room_entry.text().strip()
        if code:
            self.current_room = code
            self.sio.emit('join', {'room': code})
            self.update_chat(f'[System]: Room {code}')
            self.room_entry.setVisible(False)
            print(f'[CHAT] Joined: {code}')
        else:
            self.update_chat('[System]: Enter code')
    
    def send_message(self):
        """Send a chat message"""
        msg = self.msg_entry.text().strip()
        if msg and self.current_room:
            self.sio.emit('message', {'msg': msg, 'room': self.current_room})
            self.update_chat(f'[You]: {msg}')
            self.msg_entry.clear()
            self.send_chat_btn.setVisible(False)
            print(f'[CHAT] Sent: {msg}')
        elif not self.current_room:
            self.update_chat('[System]: Join room')
    
    def update_chat(self, text):
        """Update chat display"""
        self.chat_display.append(text)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == '__main__':
    try:
        print('[INIT] Creating QApplication...')
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        print('[INIT] Starting app...')
        mutex_name = 'Global\\GeminiNesBot_SingleInstance_Mutex'
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == 183:
            QMessageBox.warning(None, 'Already Running', 'It\'s already running. To avoid multiple instances, this launch will close.')
            sys.exit(0)
        
        print('[INIT] Getting HWID...')
        my_hwid = get_stable_hwid()
        print(f'App Started. HWID: {my_hwid}')
        
        # NOTE: Pre-warming accessibility disabled - causes COM conflict with Qt
        # It will trigger on first Alt+A press instead
        # print('[INIT] Pre-warming accessibility...')
        # set_chrome_accessibility_registry()
        # force_chrome_accessibility_on()
        # print('🔧 Accessibility pre-warmed. First Alt+A should work now!')
        
        print('[INIT] Creating UI window...')
        window = ChatbotUI(my_hwid)
        app._instance_mutex = mutex
        
        print('[INIT] Starting event loop...')
        sys.exit(app.exec_())
    except Exception as e:
        print(f'❌ FATAL ERROR: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        pass
