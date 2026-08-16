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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
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
        
        # Headless mode - default False for Windows
        self.headless = os.environ.get('HEADLESS', 'false').lower() == 'true'
        
        # Pre-compile regex patterns
        self._patterns = [
            r'font-size:\s*28px[^>]*>(\d{6})</div>',
            r'verification code[:\s]+(\d{6})',
            r'code[:\s]+(\d{6})',
            r'>(\d{6})<',
            r'\b(\d{6})\b'
        ]
        self._compiled_patterns = [re.compile(p) for p in self._patterns]
        
        # Session reuse
        self._session = requests.Session()
        
    def create_temp_inbox(self):
        """Create temporary email inbox"""
        logging.info("📧 Creating temporary email...")
        response = self._session.post(self.temp_api, timeout=10)
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
    
    def wait_for_otp_browser(self, timeout=120):
        """Wait for OTP from temp email"""
        logging.info(f"📨 Waiting for OTP in email...")
        
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            try:
                url = f"{self.wait_api}/{self.token}/wait"
                params = {"timeout": 1}
                
                response = self._session.get(url, params=params, timeout=5)
                data = response.json()
                
                if data.get('emails'):
                    for email in data['emails']:
                        if 'vmoscloud' in email.get('from', '').lower():
                            code = self.extract_verification_code(email)
                            if code:
                                logging.info(f"\n✅ OTP: {code}")
                                return code
                
                elapsed = int(time.perf_counter() - start_time)
                logging.info(f"⏳ Waiting... {elapsed}s / {timeout}s", end="\r")
                time.sleep(1)
                
            except KeyboardInterrupt:
                logging.warning("⚠️ Waiting cancelled")
                return None
            except:
                time.sleep(1)
        
        logging.error("❌ OTP timeout")
        return None
    
    def wait_for_new_otp(self, timeout=120):
        """Wait for a NEW OTP"""
        logging.info(f"📨 Waiting for NEW OTP for password change...")
        
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            try:
                url = f"{self.wait_api}/{self.token}/wait"
                params = {"timeout": 1}
                
                response = self._session.get(url, params=params, timeout=5)
                data = response.json()
                
                if data.get('emails'):
                    for email in data['emails']:
                        if 'vmoscloud' in email.get('from', '').lower():
                            code = self.extract_verification_code(email)
                            if code:
                                logging.info(f"\n✅ NEW OTP: {code}")
                                return code
                
                elapsed = int(time.perf_counter() - start_time)
                logging.info(f"⏳ Waiting for NEW OTP... {elapsed}s / {timeout}s", end="\r")
                time.sleep(1)
                
            except KeyboardInterrupt:
                logging.warning("⚠️ Waiting cancelled")
                return None
            except:
                time.sleep(1)
        
        logging.error("❌ NEW OTP timeout")
        return None
    
    def extract_verification_code(self, email_data):
        """Extract verification code from email"""
        html = email_data.get('html', '')
        body = email_data.get('body', '')
        
        full_text = f"{body} {html}"
        
        for pattern in self._compiled_patterns:
            match = pattern.search(full_text)
            if match:
                code = match.group(1)
                if len(code) == 6 and code.isdigit():
                    return code
        return None
    
    def get_captcha_solver_script(self):
        """Get the Tampermonkey CAPTCHA solver script"""
        return """
// ==UserScript==
// @name         Universal CAPTCHA Solver
// @version      27.0
// @match        https://cloud.vmoscloud.com/*
// @run-at       document-end
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🔥 CAPTCHA Solver v27.0 loaded');
    
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
        console.log('🎯 Solving CAPTCHA...');
        await delay(1000);
        
        const { slider, track, puzzle, indicator } = getCaptchaElements();
        if (!slider || !track) {
            console.log('❌ Elements not found');
            return false;
        }
        
        if (isCaptchaSolved()) {
            console.log('✅ Already solved!');
            return true;
        }
        
        const trackRect = track.getBoundingClientRect();
        const sliderRect = slider.getBoundingClientRect();
        const trackWidth = trackRect.width;
        const sliderWidth = sliderRect.width;
        const maxDistance = trackWidth - sliderWidth - 6;
        
        console.log(`📏 Track: ${trackWidth}px, Max: ${maxDistance}px`);
        
        const positions = [0.65, 0.70, 0.75, 0.80, 0.85];
        
        for (const pos of positions) {
            if (isCaptchaSolved()) break;
            
            const targetLeft = maxDistance * pos;
            console.log(`🔄 Trying ${Math.round(pos * 100)}%: ${targetLeft.toFixed(1)}px`);
            
            slider.style.left = '0px';
            if (puzzle) puzzle.style.left = '0px';
            if (indicator) indicator.style.width = '0px';
            await delay(300);
            
            const startX = sliderRect.left + sliderWidth / 2;
            const startY = sliderRect.top + sliderRect.height / 2;
            
            const mouseDown = new MouseEvent('mousedown', {
                clientX: startX, clientY: startY, bubbles: true
            });
            slider.dispatchEvent(mouseDown);
            
            await delay(100);
            
            const steps = 30 + Math.floor(Math.random() * 20);
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
                
                await delay(10 + Math.random() * 20);
            }
            
            const mouseUp = new MouseEvent('mouseup', {
                clientX: startX + targetLeft + sliderWidth / 2,
                clientY: startY,
                bubbles: true
            });
            document.dispatchEvent(mouseUp);
            
            await delay(1500);
            
            if (isCaptchaSolved()) {
                console.log(`✅ SOLVED at ${Math.round(pos * 100)}%!`);
                return true;
            }
            
            const refresh = document.querySelector('#aliyunCaptcha-btn-refresh');
            if (refresh) {
                refresh.click();
                await delay(2000);
            }
        }
        
        console.log('❌ Failed to solve');
        return false;
    }
    
    let isSolving = false;
    
    function monitor() {
        setInterval(async () => {
            if (isSolving) return;
            if (isPopupVisible()) {
                console.log('🔔 CAPTCHA detected!');
                isSolving = true;
                await solveCaptcha();
                isSolving = false;
            }
        }, 1000);
    }
    
    window.captchaSolver = {
        solve: solveCaptcha,
        status: isCaptchaSolved,
        ready: true
    };
    
    setTimeout(monitor, 1000);
    console.log('✅ CAPTCHA solver ready!');
    
})();
"""
    
    def setup_browser(self):
        """Setup Chrome browser"""
        logging.info("🌐 Starting browser...")
        
        is_windows = os.name == 'nt'
        
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1200,800")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Only use headless if explicitly requested
        if self.headless:
            logging.info("Running in headless mode")
            options.add_argument("--headless=new")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--disable-setuid-sandbox")
            options.add_argument("--disable-software-rasterizer")
            if is_windows:
                options.add_argument("--disable-gpu")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logging.warning(f"⚠️ WebDriver manager failed: {e}")
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.set_page_load_timeout(20)
        self.driver.implicitly_wait(5)
        logging.info("✅ Browser ready!")
        return self.driver
    
    def inject_captcha_solver(self):
        """Inject the CAPTCHA solver script"""
        script = self.get_captcha_solver_script()
        self.driver.execute_script(f"""
            const script = document.createElement('script');
            script.textContent = arguments[0];
            document.documentElement.appendChild(script);
        """, script)
        logging.info("✅ CAPTCHA solver injected!")
    
    def enter_email(self, email):
        """Enter email"""
        logging.info(f"📧 Entering email: {email}")
        
        try:
            email_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".el-input__inner"))
            )
            
            self.driver.execute_script("arguments[0].click();", email_input)
            time.sleep(0.1)
            self.driver.execute_script("arguments[0].value = '';", email_input)
            time.sleep(0.05)
            self.driver.execute_script(f"arguments[0].value = '{email}';", email_input)
            time.sleep(0.05)
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
        """Click the Login/Register button"""
        logging.info("🖱️ Clicking login button...")
        
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
        """Enter OTP into the 6 separate digit boxes"""
        logging.info(f"🔑 Entering OTP: {otp}")
        
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
        
        otp_str = str(otp)
        
        for i, digit in enumerate(otp_str):
            try:
                self.driver.execute_script("arguments[0].click();", otp_inputs[i])
                time.sleep(0.05)
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
    
    def wait_for_captcha(self, timeout=60):
        """Wait for CAPTCHA to be solved"""
        logging.info("\n⏳ Waiting for CAPTCHA...")
        time.sleep(1)
        
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
        
        start = time.perf_counter()
        while time.perf_counter() - start < timeout:
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
            time.sleep(1)
        
        logging.warning("⚠️ CAPTCHA not solved automatically")
        return False
    
    def request_password_change_otp(self, email):
        """Request a NEW OTP for password change"""
        logging.info(f"\n📨 Requesting NEW OTP for password change...")
        
        try:
            url = f"{self.vmos_api}/api/sms/smsSend"
            payload = {
                "smsType": 6,
                "mobilePhone": email
            }
            
            logging.info(f"  📡 URL: {url}")
            logging.info(f"  📦 Payload: {payload}")
            
            response = self._session.post(url, json=payload, timeout=10, verify=False)
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
        """Change password using the API"""
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
            response = self._session.post(url, json=payload, timeout=15, verify=False)
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
        """Save account to file"""
        try:
            with open('vmos_accounts.txt', 'a') as f:
                f.write(f"{email} | {otp} | {password if password else 'NO_PASSWORD_SET'} | {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            logging.info(f"💾 Account saved to vmos_accounts.txt")
            return True
        except Exception as e:
            logging.error(f"❌ Error saving account: {e}")
            return False
    
    def register(self):
        """Complete registration flow"""
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
            time.sleep(2)
            
            self.inject_captcha_solver()
            time.sleep(1)
            
            if not self.enter_email(email):
                logging.error("Failed to enter email")
                return None
            
            if not self.click_login_button():
                logging.error("Failed to click login button")
                return None
            
            if not self.wait_for_captcha():
                logging.warning("CAPTCHA not solved, continuing anyway...")
            
            logging.info("\n📨 Waiting for OTP email...")
            otp = self.wait_for_otp_browser(timeout=90)
            
            if not otp:
                logging.error("No OTP received")
                return None
            
            time.sleep(1)
            if not self.enter_otp_digit_boxes(otp):
                logging.error("Failed to enter OTP")
                return None
            
            logging.info("\n⏳ Waiting 3 seconds for registration to process...")
            time.sleep(3)
            
            new_password = self.generate_password()
            logging.info(f"\n🔑 Generated password: {new_password}")
            
            logging.info("\n" + "=" * 60)
            logging.info("🔐 REQUESTING NEW OTP FOR PASSWORD CHANGE...")
            logging.info("=" * 60)
            
            otp_requested = self.request_password_change_otp(email)
            
            if otp_requested:
                logging.info("\n📨 Waiting for NEW OTP...")
                new_otp = self.wait_for_new_otp(timeout=60)
                
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
    # Run once for Windows
    result = main()