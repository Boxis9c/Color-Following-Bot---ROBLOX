import pygetwindow as gw
import win32gui
import win32con
import pyautogui
import time
from PIL import Image
import numpy as np
from pynput.keyboard import Key, Controller
import pyperclip

keyboard = Controller()

# Target color to search for (can be changed)
TARGET_COLOR = "Blue"  # Change this to detect different colors
COLOR_LIST = ["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Cyan", "Magenta"]
current_color_index = 0

# Track current key states
current_turn_key = None
current_forward = False
last_color_switch_time = time.time()  # Track when we last switched colors

def find_roblox_window():
    """
    Find Roblox window by searching for windows containing 'Roblox' in the title.
    Returns the window object if found, None otherwise.
    """
    try:
        windows = gw.getAllWindows()
        
        for window in windows:
            if 'roblox' in window.title.lower():
                return window
        
        return None
    except Exception as e:
        print(f"Error finding window: {e}")
        return None

def focus_window(window):
    """
    Focus on the given window using win32gui.
    """
    try:
        hwnd = window._hWnd
        
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        win32gui.SetForegroundWindow(hwnd)
        
        print(f"Successfully focused on window: {window.title}")
        return True
    except Exception as e:
        print(f"Error focusing window: {e}")
        return False

def is_color_match(rgb, target_color):
    """
    Check if RGB values match the target color.
    Excludes black, white, and gray colors.
    More sensitive - detects colors on the spectrum.
    """
    r, g, b = rgb
    
    # Filter out black, white, and gray (map colors)
    # Gray check: all RGB values are similar (more lenient now)
    if abs(r - g) < 50 and abs(g - b) < 50 and abs(r - b) < 50:
        # But allow if one channel is clearly higher (colored grays)
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        if max_val - min_val < 30:
            return False  # It's gray/black/white
    
    # Black check (darker)
    if r < 50 and g < 50 and b < 50:
        return False
    
    # White check (brighter)
    if r > 220 and g > 220 and b > 220:
        return False
    
    # More lenient color detection with spectrum support
    color_ranges = {
        "Red": (r > 80 and r > g + 30 and r > b + 30),  # Detects red spectrum
        "Green": (g > 80 and g > r + 30 and g > b + 30),  # Detects green spectrum
        "Blue": (b > 80 and b > r + 30 and b > g + 30),  # Detects blue spectrum
        "Yellow": (r > 120 and g > 120 and b < 120 and r + g > 2 * b + 50),  # Yellow spectrum
        "Orange": (r > 120 and g > 50 and r > g + 20 and b < 100),  # Orange spectrum
        "Purple": (r > 70 and b > 70 and (r + b) > 2 * g + 40),  # Purple/violet spectrum
        "Cyan": (g > 80 and b > 80 and (g + b) > 2 * r + 40),  # Cyan spectrum
        "Magenta": (r > 80 and b > 80 and (r + b) > 2 * g + 40),  # Magenta/pink spectrum
    }
    
    return color_ranges.get(target_color, False)

def find_color_position(window, target_color):
    """
    Find the position of the target color in the window.
    Returns (x, y, size) where x, y are relative to window center, size is pixel count.
    """
    try:
        x, y, width, height = window.left, window.top, window.width, window.height
        
        # Take screenshot
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        img_array = np.array(screenshot)
        
        # Find pixels matching the target color
        matching_pixels = []
        
        # Sample every 5th pixel for performance
        for i in range(0, img_array.shape[0], 5):
            for j in range(0, img_array.shape[1], 5):
                pixel = img_array[i, j]
                if is_color_match(pixel, target_color):
                    matching_pixels.append((j, i))  # (x, y)
        
        if not matching_pixels:
            return None, None, 0
        
        # Calculate center of matching pixels (weighted by concentration)
        pixels_array = np.array(matching_pixels)
        center_x = int(pixels_array[:, 0].mean())
        center_y = int(pixels_array[:, 1].mean())
        
        # Get position relative to window center
        window_center_x = width // 2
        window_center_y = height // 2
        
        relative_x = center_x - window_center_x
        relative_y = center_y - window_center_y
        
        return relative_x, relative_y, len(matching_pixels)
        
    except Exception as e:
        print(f"Error finding color: {e}")
        return None, None, 0

def switch_to_next_color():
    """
    Switch to the next color in the rotation and announce it.
    """
    global current_color_index, TARGET_COLOR, last_color_switch_time
    
    # Move to next color
    current_color_index = (current_color_index + 1) % len(COLOR_LIST)
    TARGET_COLOR = COLOR_LIST[current_color_index]
    last_color_switch_time = time.time()
    
    print(f"\n{'='*50}")
    print(f"🔄 SWITCHING COLOR TO: {TARGET_COLOR}")
    print(f"{'='*50}\n")
    
    # Announce in chat
    announce_in_chat(f"Now following {TARGET_COLOR}")
    
    return TARGET_COLOR

def release_all_keys():
    """
    Release all currently pressed keys.
    """
    global current_turn_key, current_forward
    
    if current_turn_key:
        keyboard.release(current_turn_key)
        current_turn_key = None
    
    if current_forward:
        keyboard.release(Key.up)
        current_forward = False

def announce_in_chat(message):
    """
    Announce a message in Roblox chat by pressing /, typing message, and hitting enter.
    """
    try:
        print(f"  📢 Attempting to announce: {message}")
        
        # Release all keys first
        release_all_keys()
        
        time.sleep(0.1)
        
        # Press / to open chat
        keyboard.press('/')
        time.sleep(0.05)
        keyboard.release('/')
        
        time.sleep(0.15)
        
        # Copy message to clipboard
        pyperclip.copy(message)
        print(f"  📋 Copied to clipboard: {message}")
        
        time.sleep(0.1)
        
        # Paste using Ctrl+V
        keyboard.press(Key.ctrl)
        time.sleep(0.05)
        keyboard.press('v')
        time.sleep(0.05)
        keyboard.release('v')
        time.sleep(0.05)
        keyboard.release(Key.ctrl)
        
        time.sleep(0.15)
        
        # Press Enter to send
        keyboard.press(Key.enter)
        time.sleep(0.05)
        keyboard.release(Key.enter)
        
        time.sleep(0.2)
        
        print(f"  ✓ Chat announcement sent!")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to announce in chat: {e}")
        return False
    """
    Release all currently pressed keys.
    """
    global current_turn_key, current_forward
    
    if current_turn_key:
        keyboard.release(current_turn_key)
        current_turn_key = None
    
    if current_forward:
        keyboard.release(Key.up)
        current_forward = False

def start_turning(direction):
    """
    Start continuously turning in a direction.
    """
    global current_turn_key
    
    # Release previous turn key if different
    if current_turn_key and current_turn_key != direction:
        keyboard.release(current_turn_key)
    
    # Press new direction
    if current_turn_key != direction:
        keyboard.press(direction)
        current_turn_key = direction

def start_walking():
    """
    Start walking forward continuously.
    """
    global current_forward
    
    if not current_forward:
        keyboard.press(Key.up)
        current_forward = True

def stop_walking():
    """
    Stop walking forward.
    """
    global current_forward
    
    if current_forward:
        keyboard.release(Key.up)
        current_forward = False

def navigate_to_color(window, target_color):
    """
    Navigate towards the target color by continuously turning and walking.
    """
    global current_turn_key
    
    relative_x, relative_y, pixel_count = find_color_position(window, target_color)
    
    # Require minimum pixel count to avoid false positives (lowered threshold)
    min_pixel_threshold = 5
    
    # If no color found or too small, turn to search
    if relative_x is None or pixel_count < min_pixel_threshold:
        if pixel_count > 0 and pixel_count < min_pixel_threshold:
            print(f"  {target_color} too small ({pixel_count} pixels) - TURNING RIGHT to search")
        else:
            print(f"  {target_color} NOT FOUND - TURNING RIGHT to search")
        
        # Always turn right when searching
        stop_walking()
        start_turning(Key.right)
        return False
    
    print(f"  {target_color} at offset ({relative_x:4d}, {relative_y:4d}), pixels: {pixel_count}")
    
    # Check if color is centered (within 60 pixels of middle)
    if abs(relative_x) <= 60:
        # Color is centered - WALK FORWARD
        print(f"  → {target_color} CENTERED ({relative_x}px off) - WALKING FORWARD!")
        # Stop any turning
        if current_turn_key:
            keyboard.release(current_turn_key)
            current_turn_key = None
        # Start walking
        start_walking()
        return True
    
    # Color is NOT centered - turn towards it
    stop_walking()  # Stop walking while turning
    
    if relative_x > 0:
        # Color is on the RIGHT side - turn RIGHT
        print(f"  → Color is on RIGHT ({relative_x}px) - TURNING RIGHT")
        start_turning(Key.right)
    else:
        # Color is on the LEFT side - turn LEFT
        print(f"  → Color is on LEFT ({relative_x}px) - TURNING LEFT")
        start_turning(Key.left)
    
    return False

def main():
    """
    Main function to detect Roblox and navigate to target color.
    """
    global TARGET_COLOR, last_color_switch_time
    
    print(f"Searching for Roblox window...")
    
    # Find Roblox window
    roblox_window = find_roblox_window()
    
    if not roblox_window:
        print("Roblox window not found. Make sure Roblox is running!")
        return
    
    print(f"Found Roblox window: {roblox_window.title}")
    
    # Focus on the window
    if not focus_window(roblox_window):
        print("Failed to focus on Roblox window.")
        return
    
    print("Roblox window is now focused!")
    print(f"\nBot will rotate through colors every 60 seconds:")
    print(f"Colors: {', '.join(COLOR_LIST)}")
    print("Press Ctrl+C to stop.\n")
    
    time.sleep(2)  # Give time for window to be ready
    
    # Announce initial color
    print(f"Starting with color: {TARGET_COLOR}")
    announce_in_chat(f"Now following {TARGET_COLOR}")
    
    time.sleep(0.5)
    
    try:
        iteration = 1
        next_switch_time = time.time() + 60  # First switch in 60 seconds
        
        while True:
            # Check if it's time to switch colors
            current_time = time.time()
            time_until_switch = next_switch_time - current_time
            
            if current_time >= next_switch_time:
                print(f"\n⏰ 60 seconds elapsed! Switching color now...")
                switch_to_next_color()
                next_switch_time = time.time() + 60  # Schedule next switch
                time.sleep(1)  # Pause after switching
            
            # Refresh window object
            roblox_window = find_roblox_window()
            
            if not roblox_window:
                print("Roblox window lost. Searching again...")
                release_all_keys()
                time.sleep(5)
                continue
            
            # Show time until next switch every 10 scans
            if iteration % 10 == 0:
                print(f"[Scan #{iteration}] Following: {TARGET_COLOR} | Next switch in: {int(time_until_switch)}s")
            else:
                print(f"[Scan #{iteration}] Following: {TARGET_COLOR}")
            
            navigate_to_color(roblox_window, TARGET_COLOR)
            
            iteration += 1
            
            # Small delay between scans
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nNavigation stopped by user.")
        print("Releasing all keys...")
        release_all_keys()
        print(f"Total scans: {iteration - 1}")

if __name__ == "__main__":
    main()