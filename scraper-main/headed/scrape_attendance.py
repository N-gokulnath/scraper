from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import json, time, os, re, shutil
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

PORTAL_URL = "https://gnc-egovernance.com/student/"
SCREENSHOT_DIR = "screenshots"

def get_credentials():
    try:
        with open("credentails.txt", "r") as f:
            content = f.read()
            uid = re.search(r'user id:"(.*?)"', content).group(1)
            pwd = re.search(r'password:"(.*?)"', content).group(1)
            return uid, pwd
    except Exception as e:
        print(f"Error loading credentails.txt: {e}")
        return None, None

USER_ID, PASSWORD = get_credentials()

# Clear previous screenshots at the start
if os.path.exists(SCREENSHOT_DIR):
    shutil.rmtree(SCREENSHOT_DIR)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_screenshot(driver, name):
    f = f"{SCREENSHOT_DIR}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    driver.save_screenshot(f)
    print(f"Screenshot: {f}")

def login(driver):
    if not USER_ID or not PASSWORD:
        print("Credentials not found. Please check credentails.txt")
        return
    print("\n=== LOGGING IN ===")
    driver.get(PORTAL_URL)
    wait = WebDriverWait(driver, 15)
    username = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password = driver.find_element(By.ID, "passwd")
    username.send_keys(USER_ID)
    password.send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//input[@type='submit']").click()
    wait.until(EC.presence_of_element_located((By.ID, "admenu")))
    print("Login successful.")

def navigate_to_attendance(driver):
    print("\n=== NAVIGATING TO ATTENDANCE ===")
    wait = WebDriverWait(driver, 15)
    
    print("Opening Masters menu...")
    masters_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.masters")))
    masters_btn.click()
    time.sleep(2)
    
    print("Clicking Student Attendance...")
    try:
        attendance_item = wait.until(EC.element_to_be_clickable((By.ID, "mnu-18:1")))
        attendance_item.click()
    except:
        attendance_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Student Attendance')]")))
        attendance_item.click()
    
    print("Waiting for attendance grid...")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "x-grid3-body")))
    time.sleep(5)
    save_screenshot(driver, "attendance_view")

def extract(driver):
    print("\n=== EXTRACTING DATA ===")
    
    # Expand all month groups (clicking the header to toggle)
    # This targets the group header divs which often contain the toggle logic
    print("Expanding all month groups...")
    driver.execute_script("""
        var headers = document.querySelectorAll('.x-grid-group-hd');
        headers.forEach(function(h) {
            if (h.parentElement.classList.contains('x-grid-group-collapsed')) {
                h.click();
            }
        });
    """)
    time.sleep(3)
    
    groups = driver.find_elements(By.CLASS_NAME, "x-grid-group")
    data = []
    total_inst = 0
    total_pres = 0
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_info = {
        "posted": False, 
        "hours": 0, 
        "p1": "N/A", 
        "p2": "N/A", 
        "p3": "N/A", 
        "p4": "N/A", 
        "p5": "N/A",
        "found": False
    }
    
    print(f"Searching for date: {today_date}")
    
    for group in groups:
        try:
            # We use get_attribute('textContent') to read content even if not perfectly visible to Selenium's .text
            title_elem = group.find_element(By.CLASS_NAME, "x-grid-group-title")
            title = title_elem.get_attribute("textContent").strip()
            
            summary_row = group.find_element(By.CLASS_NAME, "x-grid3-summary-row")
            summary_text = summary_row.get_attribute("textContent").strip()
            
            hours = re.findall(r'(\d+)\s+hours', summary_text)
            if len(hours) >= 3:
                ti, ab, pr = int(hours[0]), int(hours[1]), int(hours[2])
                total_inst += ti
                total_pres += pr
                data.append({
                    "month": title, 
                    "perc": f"{(pr/ti*100):.2f}%" if ti > 0 else "0%", 
                    "pres": pr, 
                    "total": ti
                })
            
            # Check for today's row inside this group
            rows = group.find_elements(By.CLASS_NAME, "x-grid3-row")
            for row in rows:
                # Use class names for columns to be more precise
                # Column 0 is Date: x-grid3-td-Date or similar. 
                # According to common ExtJS patterns it's often indexed classes like x-grid3-col-0, x-grid3-col-1 etc.
                # But let's look for the cell inner divs
                cells = row.find_elements(By.CLASS_NAME, "x-grid3-cell-inner")
                if not cells: continue
                
                row_date = cells[0].get_attribute("textContent").strip()
                
                if today_date in row_date:
                    print(f"Found match for today: {row_date}")
                    today_info["p1"] = cells[1].get_attribute("textContent").strip() or "N/A"
                    today_info["p2"] = cells[2].get_attribute("textContent").strip() or "N/A"
                    today_info["p3"] = cells[3].get_attribute("textContent").strip() or "N/A"
                    today_info["p4"] = cells[4].get_attribute("textContent").strip() or "N/A"
                    today_info["p5"] = cells[5].get_attribute("textContent").strip() or "N/A"
                    
                    total_h_str = cells[6].get_attribute("textContent").strip()
                    h_match = re.search(r'(\d+)', total_h_str)
                    curr_h = int(h_match.group(1)) if h_match else 0
                    
                    today_info["hours"] = curr_h
                    today_info["found"] = True
                    if curr_h >= 5: today_info["posted"] = True
                    
        except Exception as e:
            # print(f"Error in group: {e}")
            continue

    overall = (total_pres / total_inst * 100) if total_inst > 0 else 0
    return {
        "monthly": data, 
        "overall": f"{overall:.2f}%", 
        "total_p": total_pres, 
        "total_i": total_inst, 
        "today": today_info
    }

def main():
    print("="*60)
    print("ATTENDANCE PRO - FINAL REPORT")
    print("="*60)
    
    options = webdriver.ChromeOptions()
    # Add flag to handle encoding if needed, though print() usually handles it
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        login(driver)
        navigate_to_attendance(driver)
        res = extract(driver)
        
        print(f"\nOVERALL ATTENDANCE: {res['overall']}")
        print(f"Total: {res['total_p']} / {res['total_i']} hours\n")
        
        print("MONTHLY DETAILS:")
        for m in res['monthly']:
            print(f" - {m['month']}: {m['perc']} ({m['pres']}/{m['total']} hrs)")
            
        print("\n" + "*"*40)
        print(f"TODAY ({datetime.now().strftime('%Y-%m-%d')}) CHECK:")
        if not res['today']['found']:
            print("Status: [X] - DATE NOT FOUND IN TABLE")
        else:
            status = "YES, 5 hours posted! [OK]" if res['today']['posted'] else "NO, 5 hours not fully posted yet. [X]"
            print(f"Status: {status}")
            print(f"Hours recorded: {res['today']['hours']}")
            print(f"Period 1: {res['today']['p1']}")
            print(f"Period 2: {res['today']['p2']}")
            print(f"Period 3: {res['today']['p3']}")
            print(f"Period 4: {res['today']['p4']}")
            print(f"Period 5: {res['today']['p5']}")
        print("*"*40)

        with open("attendance_final.json", "w") as f:
            json.dump(res, f, indent=2)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        save_screenshot(driver, "final_error")
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
