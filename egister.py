import time
import re
import json
import os
import requests
import hashlib
import urllib3
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging for Render - REDUCED FOR SPEED
logging.basicConfig(
    level=logging.WARNING,  # Faster: WARNING instead of INFO
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class VMOSCloudBrowserRegister:
    def __init__(self):
        self.temp_api = "https://api.tempmail.lol/v2/inbox/create"
        self.wait_api = "https://api.tempmail.lol/v3/inboxes"
        self.vmos_url = "https://cloud.vmoscloud.com/login"
        self.vmos_api = "https://api.vmoscloud.com/vcpcloud"
        
        self.email = None
        self.token = None
        self.driver = None
        self.password = None
        
        # Headless mode for Render
        self.headless = os.environ.get('HEADLESS', 'true').lower() == 'true'
        
        # Pre-compile regex patterns for speed (faster than re.search each time)
        self.code_patterns = [
            re.compile(r'font-size:\s*28px[^>]*>(\d{6})</div>'),
            re.compile(r'verification code[:\s]+(\d{6})'),
            re.compile(r'code[:\s]+(\d{6})'),
            re.compile(r'>(\d{6})<'),
            re.compile(r'\b(\d{6})\b')
        ]
        
    def create_temp_inbox(self):
        """Create temporary email inbox"""
        response = requests.post(self.temp_api)
        data = response.json()
        
        self.email = data['address']
        self.token = data['token']
        
        logging.info(f"✅ Email: {self.email}")
        return self.email
    
    def generate_password(self):
        """Generate a random password"""
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(12))
        self.password = password
        return password
    
    def wait_for_otp_browser(self, timeout=60):  # Reduced from 120 to 60
        """Wait for OTP from temp email - OPTIMIZED"""
        start_time = time.time()
        wait_time = 1  # Reduced from 2 to 1 second
        
        while time.time() - start_time < timeout:
            try:
                url = f"{self.wait_api}/{self.token}/wait"
                params = {"timeout": 1}  # Reduced from 3 to 1
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if data.get('emails'):
                    for email in data['emails']:
                        if 'vmoscloud' in email.get('from', '').lower():
                            code = self.extract_verification_code(email)
                            if code:
                                logging.info(f"✅ OTP: {code}")
                                return code
                
                elapsed = int(time.time() - start_time)
                if elapsed % 5 == 0:  # Log every 5 seconds instead of every time
                    logging.info(f"⏳ Waiting... {elapsed}s / {timeout}s")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logging.warning("⚠️ Waiting cancelled")
                return None
            except:
                time.sleep(wait_time)
        
        logging.error("❌ OTP timeout")
        return None
    
    def wait_for_new_otp(self, timeout=60):  # Reduced from 120 to 60
        """Wait for a NEW OTP - OPTIMIZED"""
        start_time = time.time()
        wait_time = 1
        
        while time.time() - start_time < timeout:
            try:
                url = f"{self.wait_api}/{self.token}/wait"
                params = {"timeout": 1}  # Reduced from 3 to 1
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if data.get('emails'):
                    for email in data['emails']:
                        if 'vmoscloud' in email.get('from', '').lower():
                            code = self.extract_verification_code(email)
                            if code:
                                logging.info(f"✅ NEW OTP: {code}")
                                return code
                
                elapsed = int(time.time() - start_time)
                if elapsed % 5 == 0:  # Log every 5 seconds
                    logging.info(f"⏳ Waiting for NEW OTP... {elapsed}s / {timeout}s")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logging.warning("⚠️ Waiting cancelled")
                return None
            except:
                time.sleep(wait_time)
        
        logging.error("❌ NEW OTP timeout")
        return None
    
    def extract_verification_code(self, email_data):
        """Extract verification code from email - OPTIMIZED with pre-compiled patterns"""
        html = email_data.get('html', '')
        body = email_data.get('body', '')
        
        full_text = f"{body} {html}"
        
        # Use pre-compiled patterns for speed
        for pattern in self.code_patterns:
            match = pattern.search(full_text)
            if match:
                code = match.group(1)
                if len(code) == 6 and code.isdigit():
                    return code
        return None
    
    def get_captcha_solver_script(self):
        """Get the Tampermonkey CAPTCHA solver script - OPTIMIZED"""
        return """
// ==UserScript==
// @name         Universal CAPTCHA Solver
// @version      27.1
// @match        https://cloud.vmoscloud.com/*
// @run-at       document-end
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
    
    function getCaptchaElements() {
        const puzzle = document.querySelector('#aliyunCaptcha-puzzle');
        const slider = document.querySelector('#aliyunCaptcha-sliding-slider');
        const track = document.querySelector('#aliyunCaptcha-sliding-body');
        const indicator = document.querySelector('#aliyunCaptcha-sliding-left');
        const text = document.querySelector('#aliyunCaptcha-sliding-text');
        const popup = document.querySelector('#aliyunCaptcha-window-popup');
        const refresh = document.querySelector('#aliyunCaptcha-btn-refresh');
        return { puzzle, slider, track, indicator, text, popup, refresh };
    }
    
    function isCaptchaSolved() {
        const bodyEl = document.querySelector('#aliyunCaptcha-sliding-body');
        if (bodyEl && bodyEl.className.includes('verified')) {
            return true;
        }
        const text = document.querySelector('#aliyunCaptcha-sliding-text');
        if (text && text.textContent.includes('Verified')) {
            return true;
        }
        return false;
    }
    
    function isPopupVisible() {
        const popup = document.querySelector('#aliyunCaptcha-window-popup');
        if (!popup) return false;
        const style = getComputedStyle(popup);
        if (style.display === 'none') return false;
        return popup.classList.contains('window-show');
    }
    
    async function solveCaptcha() {
        await delay(500);  // Reduced from 1000 to 500
        
        const { slider, track, puzzle, indicator } = getCaptchaElements();
        if (!slider || !track) {
            return false;
        }
        
        if (isCaptchaSolved()) {
            return true;
        }
        
        const trackRect = track.getBoundingClientRect();
        const sliderRect = slider.getBoundingClientRect();
        const trackWidth = trackRect.width;
        const sliderWidth = sliderRect.width;
        const maxDistance = trackWidth - sliderWidth - 6;
        
        const positions = [0.70, 0.80, 0.75];  // Reduced from 5 to 3 positions
        
        for (const pos of positions) {
            if (isCaptchaSolved()) break;
            
            const targetLeft = maxDistance * pos;
            
            slider.style.left = '0px';
            if (puzzle) puzzle.style.left = '0px';
            if (indicator) indicator.style.width = '0px';
            await delay(200);  // Reduced from 300 to 200
            
            const startX = sliderRect.left + sliderWidth / 2;
            const startY = sliderRect.top + sliderRect.height / 2;
            
            const mouseDown = new MouseEvent('mousedown', {
                clientX: startX, clientY: startY, bubbles: true
            });
            slider.dispatchEvent(mouseDown);
            
            await delay(50);  // Reduced from 100 to 50
            
            const steps = 20 + Math.floor(Math.random() * 15);  // Reduced from 30+20 to 20+15
            
            for (let i = 0; i <= steps; i++) {
                const progress = i / steps;
                const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                const currentX = startX + (targetLeft + sliderWidth / 2) * eased;
                const currentY = startY + Math.sin(i * 0.3) * 0.5;
                
                const mouseMove = new MouseEvent('mousemove', {
                    clientX: currentX, clientY: currentY, bubbles: true
                });
                document.dispatchEvent(mouseMove);
                
                const newLeft = targetLeft * eased;
                slider.style.left = newLeft + 'px';
                if (puzzle) puzzle.style.left = newLeft + 'px';
                if (indicator) indicator.style.width = newLeft + 'px';
                
                await delay(5 + Math.random() * 10);  // Reduced from 10+20 to 5+10
            }
            
            const mouseUp = new MouseEvent('mouseup', {
                clientX: startX + targetLeft + sliderWidth / 2,
                clientY: startY,
                bubbles: true
            });
            document.dispatchEvent(mouseUp);
            
            await delay(1000);  // Reduced from 1500 to 1000
            
            if (isCaptchaSolved()) {
                return true;
            }
            
            const refresh = document.querySelector('#aliyunCaptcha-btn-refresh');
            if (refresh) {
                refresh.click();
                await delay(1000);  // Reduced from 2000 to 1000
            }
        }
        
        return false;
    }
    
    let isSolving = false;
    
    function monitor() {
        setInterval(async () => {
            if (isSolving) return;
            if (isPopupVisible()) {
                isSolving = true;
                await solveCaptcha();
                isSolving = false;
            }
        }, 500);  // Reduced from 1000 to 500
    }
    
    window.captchaSolver = {
        solve: solveCaptcha,
        status: isCaptchaSolved,
        ready: true
    };
    
    setTimeout(monitor, 500);  // Reduced from 1000 to 500
    
})();
"""
    
    def setup_browser(self):
        """Setup Chrome browser for Render - OPTIMIZED"""
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,800")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Speed optimizations for browser
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Will enable via page settings if needed
        
        # Headless mode for Render
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--remote-debugging-port=9222")
            # Additional headless stability
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-webgl")
            options.add_argument("--disable-accelerated-2d-canvas")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(30)  # Reduced from default 60 to 30
        return self.driver
    
    def inject_captcha_solver(self):
        """Inject the CAPTCHA solver script"""
        script = self.get_captcha_solver_script()
        self.driver.execute_script(f"""
            const script = document.createElement('script');
            script.textContent = arguments[0];
            document.documentElement.appendChild(script);
        """, script)
    
    def enter_email(self, email):
        """Enter email with correct focus and events - OPTIMIZED"""
        try:
            email_input = WebDriverWait(self.driver, 5).until(  # Reduced from 10 to 5
                EC.presence_of_element_located((By.CSS_SELECTOR, ".el-input__inner"))
            )
            
            self.driver.execute_script("arguments[0].click();", email_input)
            time.sleep(0.1)  # Reduced from 0.3 to 0.1
            self.driver.execute_script("arguments[0].value = '';", email_input)
            self.driver.execute_script(f"arguments[0].value = '{email}';", email_input)
            self.driver.execute_script("""
                var input = arguments[0];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
            """, email_input)
            
            logging.info("✅ Email entered successfully!")
            return True
            
        except Exception as e:
            logging.error(f"❌ Could not enter email: {e}")
            return False
    
    def click_login_button(self):
        """Click the Login/Register button - OPTIMIZED"""
        try:
            login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login/Register')]")
            self.driver.execute_script("arguments[0].click();", login_btn)
            logging.info("✅ Login button clicked")
            return True
        except:
            pass
        
        try:
            login_btn = self.driver.find_element(By.CSS_SELECTOR, ".el-button--primary")
            self.driver.execute_script("arguments[0].click();", login_btn)
            logging.info("✅ Login button clicked")
            return True
        except:
            pass
        
        logging.error("❌ Could not click login button!")
        return False
    
    def enter_otp_digit_boxes(self, otp):
        """Enter OTP into the 6 separate digit boxes - OPTIMIZED"""
        otp_inputs = []
        
        try:
            otp_inputs = self.driver.find_elements(By.CSS_SELECTOR, ".codes input[type='number']")
        except:
            pass
        
        if len(otp_inputs) == 0:
            try:
                otp_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[maxlength='1']")
            except:
                pass
        
        if len(otp_inputs) < 6:
            logging.error(f"❌ Found only {len(otp_inputs)} OTP boxes, need 6")
            return False
        
        logging.info(f"✅ Found {len(otp_inputs)} OTP input boxes")
        
        for i, digit in enumerate(str(otp)):
            try:
                self.driver.execute_script("arguments[0].click();", otp_inputs[i])
                self.driver.execute_script(f"arguments[0].value = '{digit}';", otp_inputs[i])
                self.driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, otp_inputs[i])
                logging.info(f"  Digit {i+1}: {digit}")
            except Exception as e:
                logging.warning(f"⚠️ Error entering digit {i+1}: {e}")
        
        try:
            otp_inputs[-1].send_keys(Keys.ENTER)
            logging.info("✅ Pressed Enter to submit")
        except:
            pass
        
        return True
    
    def wait_for_captcha(self, timeout=30):  # Reduced from 60 to 30
        """Wait for CAPTCHA to be solved - OPTIMIZED"""
        time.sleep(1)  # Reduced from 3 to 1
        
        captcha_visible = self.driver.execute_script("""
            var popup = document.querySelector('#aliyunCaptcha-window-popup');
            if (!popup) return false;
            var style = getComputedStyle(popup);
            return style.display !== 'none';
        """)
        
        if not captcha_visible:
            logging.info("✅ No CAPTCHA detected")
            return True
        
        logging.info("🔔 CAPTCHA detected! Waiting for auto-solve...")
        
        start = time.time()
        while time.time() - start < timeout:
            solved = self.driver.execute_script("""
                var body = document.querySelector('#aliyunCaptcha-sliding-body');
                if (body && body.className.includes('verified')) return true;
                var popup = document.querySelector('#aliyunCaptcha-window-popup');
                if (!popup) return true;
                var style = getComputedStyle(popup);
                return style.display === 'none';
            """)
            if solved:
                logging.info("✅ CAPTCHA solved!")
                return True
            time.sleep(1)  # Reduced from 2 to 1
        
        logging.warning("⚠️ CAPTCHA not solved automatically")
        return False
    
    def request_password_change_otp(self, email):
        """Request a NEW OTP for password change - OPTIMIZED"""
        logging.info(f"\n📨 Requesting NEW OTP for password change...")
        
        try:
            url = f"{self.vmos_api}/api/sms/smsSend"
            payload = {
                "smsType": 6,
                "mobilePhone": email
            }
            
            logging.info(f"  📡 URL: {url}")
            logging.info(f"  📦 Payload: {payload}")
            
            response = requests.post(url, json=payload, timeout=5, verify=False)  # Reduced from 10 to 5
            data = response.json()
            
            logging.info(f"  📨 Response: {data}")
            
            if data.get('code') == 200 or data.get('success') == True:
                logging.info(f"✅ NEW OTP requested successfully!")
                return True
            else:
                logging.warning(f"⚠️ OTP request failed: {data.get('msg', 'Unknown error')}")
                return False
                
        except Exception as e:
            logging.error(f"  ❌ Error: {e}")
            return False
    
    def change_password(self, email, otp, new_password):
        """Change password using the API - OPTIMIZED"""
        logging.info(f"\n🔐 Changing password for: {email}")
        logging.info(f"🔑 Using NEW OTP: {otp}")
        logging.info(f"🔐 New password: {new_password}")
        
        hashed_password = hashlib.md5(new_password.encode()).hexdigest()
        logging.info(f"📦 MD5 Hash: {hashed_password}")
        
        url = f"{self.vmos_api}/api/user/updateUserPasswordV2"
        payload = {
            "mobilePhone": email,
            "verifyCode": otp,
            "newPassword": hashed_password
        }
        
        logging.info(f"\n  📡 URL: {url}")
        logging.info(f"  📦 Payload: {payload}")
        
        try:
            response = requests.post(url, json=payload, timeout=5, verify=False)  # Reduced from 15 to 5
            data = response.json()
            
            logging.info(f"  📨 Response: {data}")
            
            if data.get('code') == 200 or data.get('success') == True:
                logging.info(f"✅ Password changed successfully!")
                return True
            else:
                logging.warning(f"⚠️ Password change failed: {data.get('msg', 'Unknown error')}")
                return False
                
        except Exception as e:
            logging.error(f"  ❌ Error: {e}")
            return False
    
    def save_account(self, email, otp, password):
        """Save account to file - OPTIMIZED"""
        try:
            with open('vmos_accounts.txt', 'a') as f:
                f.write(f"{email} | {otp} | {password if password else 'NO_PASSWORD_SET'} | {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            logging.info(f"💾 Account saved to vmos_accounts.txt")
            return True
        except Exception as e:
            logging.error(f"❌ Error saving account: {e}")
            return False
    
    def register(self):
        """Complete registration flow using browser - OPTIMIZED"""
        logging.info("\n" + "=" * 60)
        logging.info("🚀 VMOS Cloud Browser Registration")
        logging.info("=" * 60)
        
        email = self.create_temp_inbox()
        driver = self.setup_browser()
        
        pw_changed = False
        new_password = None
        
        try:
            logging.info("🌐 Loading VMOS Cloud...")
            driver.get(self.vmos_url)
            time.sleep(2)  # Reduced from 5 to 2
            
            self.inject_captcha_solver()
            time.sleep(1)  # Reduced from 2 to 1
            
            if not self.enter_email(email):
                logging.error("Failed to enter email")
                return None
            
            if not self.click_login_button():
                logging.error("Failed to click login button")
                return None
            
            if not self.wait_for_captcha():
                logging.warning("CAPTCHA not solved, continuing anyway...")
            
            logging.info("\n📨 Waiting for OTP email...")
            otp = self.wait_for_otp_browser(timeout=60)  # Reduced from 90 to 60
            
            if not otp:
                logging.error("No OTP received")
                return None
            
            time.sleep(1)  # Reduced from 2 to 1
            if not self.enter_otp_digit_boxes(otp):
                logging.error("Failed to enter OTP")
                return None
            
            logging.info("\n⏳ Waiting 3 seconds for registration to process...")
            time.sleep(3)  # Reduced from 5 to 3
            
            # Generate new password
            new_password = self.generate_password()
            logging.info(f"\n🔑 Generated password: {new_password}")
            
            # Request NEW OTP for password change
            logging.info("\n" + "=" * 60)
            logging.info("🔐 REQUESTING NEW OTP FOR PASSWORD CHANGE...")
            logging.info("=" * 60)
            
            otp_requested = self.request_password_change_otp(email)
            
            if otp_requested:
                logging.info("\n📨 Waiting for NEW OTP...")
                new_otp = self.wait_for_new_otp(timeout=45)  # Reduced from 60 to 45
                
                if new_otp:
                    logging.info("\n" + "=" * 60)
                    logging.info("🔐 ATTEMPTING PASSWORD CHANGE WITH NEW OTP...")
                    logging.info("=" * 60)
                    
                    pw_changed = self.change_password(email, new_otp, new_password)
                    
                    if pw_changed:
                        logging.info("\n✅ PASSWORD UPDATED SUCCESSFULLY!")
                        logging.info(f"🔐 New Password: {new_password}")
                    else:
                        logging.warning("\n⚠️ Password change failed with new OTP")
                else:
                    logging.warning("\n⚠️ No NEW OTP received")
            else:
                logging.warning("\n⚠️ Could not request NEW OTP")
            
            # Save account
            self.save_account(email, otp, new_password if pw_changed else None)
            
            return {
                "success": True, 
                "email": email, 
                "otp": otp, 
                "password": new_password if pw_changed else None
            }
            
        except Exception as e:
            logging.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            logging.info("\n📌 Closing browser...")
            try:
                driver.quit()
            except:
                pass

# ===== MAIN =====
def main():
    logging.info("\n" + "=" * 60)
    logging.info("🚀 VMOS Cloud Auto Registration + Password Change")
    logging.info("=" * 60)
    logging.info("\n⚠️  This will:")
    logging.info("  1. Create a temporary email")
    logging.info("  2. Open browser and register")
    logging.info("  3. Auto-fill email, CAPTCHA, OTP")
    logging.info("  4. Request a NEW OTP for password change")
    logging.info("  5. Change password with the NEW OTP")
    logging.info("\n" + "=" * 60)
    
    bot = VMOSCloudBrowserRegister()
    result = bot.register()
    
    if result and result.get('success'):
        logging.info("\n✅ Registration complete!")
        logging.info(f"📧 Email: {result.get('email')}")
        if result.get('password'):
            logging.info(f"🔐 Password: {result.get('password')}")
        
        logging.info("\n📌 Script completed successfully!")
    else:
        logging.error("\n❌ Registration failed")
    
    return result

if __name__ == "__main__":
    # For Render, keep running
    while True:
        try:
            result = main()
            if result and result.get('success'):
                logging.info("\n⏳ Waiting 60 seconds before next account...")
                time.sleep(60)
            else:
                logging.info("\n⏳ Waiting 30 seconds before retry...")
                time.sleep(30)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)