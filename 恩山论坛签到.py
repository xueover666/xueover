"""
cron "39 12 * * *" script-path=xxx.py,tag=匹配cron用
new Env('恩山论坛签到')
"""

import os
import re
import requests
import random
import time
from datetime import datetime

# ---------------- 统一通知模块加载 ----------------
hadsend = False
send = None
try:
    from notify import send
    hadsend = True
    print("✅ 已加载notify.py通知模块")
except ImportError:
    print("⚠️  未加载通知模块，跳过通知功能")

# 配置项
enshan_cookie = os.environ.get('enshan_cookie', '')
max_random_delay = int(os.getenv("MAX_RANDOM_DELAY", "3"))
random_signin = os.getenv("RANDOM_SIGNIN", "true").lower() == "true"
privacy_mode = os.getenv("PRIVACY_MODE", "true").lower() == "true"
# 新增：重试次数配置
RETRY_TIMES = int(os.getenv("RETRY_TIMES", "3"))
# 新增：超时时间配置
TIMEOUT = int(os.getenv("TIMEOUT", "20"))

# 恩山论坛配置
BASE_URL = 'https://www.right.com.cn/forum'
CREDIT_URLS = [
    f'{BASE_URL}/home.php?mod=spacecp&ac=credit',
    f'{BASE_URL}/home.php?mod=spacecp&ac=credit&showcredit=1',
    'https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit',
    'https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1',
]
CHECKIN_URL = f'{BASE_URL}/k_misign-sign.html'

# 优化：更贴近真实浏览器的请求头
def get_random_headers():
    """生成随机且更真实的请求头"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    sec_ch_ua = [
        '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        '"Microsoft Edge";v="121", "Not=A?Brand";v="8", "Chromium";v="121"',
        '"Chromium";v="120", "Not=A?Brand";v="99", "Google Chrome";v="120"'
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': random.choice(sec_ch_ua),
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': random.choice(['"Windows"', '"macOS"', '"Linux"']),
        'DNT': '1',
        'Priority': 'u=0, i'
    }
    return headers

def mask_username(username):
    """用户名脱敏处理"""
    if not username:
        return username
    if privacy_mode:
        if len(username) <= 2:
            return '*' * len(username)
        elif len(username) <= 4:
            return username[0] + '*' * (len(username) - 2) + username[-1]
        else:
            return username[0] + '*' * 3 + username[-1]
    return username

def format_time_remaining(seconds):
    """格式化时间显示"""
    if seconds <= 0:
        return "立即执行"
    hours, minutes = divmod(seconds, 3600)
    minutes, secs = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

def wait_with_countdown(delay_seconds, task_name):
    """带倒计时的随机延迟等待"""
    if delay_seconds <= 0:
        return
    print(f"{task_name} 需要等待 {format_time_remaining(delay_seconds)}")
    remaining = delay_seconds
    while remaining > 0:
        if remaining <= 10 or remaining % 10 == 0:
            print(f"{task_name} 倒计时: {format_time_remaining(remaining)}")
        sleep_time = 1 if remaining <= 10 else min(10, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time

def notify_user(title, content):
    """统一通知函数"""
    if hadsend:
        try:
            send(title, content)
            print(f"✅ 通知发送完成: {title}")
        except Exception as e:
            print(f"❌ 通知发送失败: {e}")
    else:
        print(f"📢 {title}\n📄 {content}")

def parse_cookies(cookie_str):
    """解析Cookie字符串，支持多账号"""
    if not cookie_str:
        return []
    lines = cookie_str.strip().split('\n')
    cookies = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split('&&')
        for part in parts:
            part = part.strip()
            if part:
                cookies.append(part)
    unique_cookies = []
    for cookie in cookies:
        if cookie and cookie not in unique_cookies:
            unique_cookies.append(cookie)
    return unique_cookies

def extract_number(text):
    """从文本中提取数字"""
    if not text:
        return 0
    try:
        number_str = re.sub(r'[^\d]', '', str(text))
        return int(number_str) if number_str else 0
    except (ValueError, TypeError):
        return 0

def extract_first(text, patterns, default=None, flags=0):
    """按顺序尝试正则，返回第一个匹配到的 group(1)（strip后）。"""
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            value = match.group(1)
            return value.strip() if isinstance(value, str) else value
    return default

class EnShanSigner:
    name = "恩山论坛"

    def __init__(self, cookie: str, index: int = 1):
        self.cookie = cookie
        self.index = index
        # 优化：每次请求使用新的session和随机请求头
        self.session = self._create_session()
        
        # 用户信息
        self.user_name = None
        self.user_group = None
        self.coin_before = None
        self.point_before = None
        self.contribution = None
        self.coin_after = None
        self.point_after = None
        self.formhash = None
        self.uid = None

    def _create_session(self):
        """创建配置更完善的session"""
        session = requests.Session()
        # 禁用连接复用，避免被检测
        session.headers.update(get_random_headers())
        session.headers['Cookie'] = self.cookie
        # 配置超时和重试
        session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=requests.packages.urllib3.util.retry.Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504, 521]
            )
        ))
        return session

    def _retry_request(self, func, *args, **kwargs):
        """通用重试装饰器"""
        last_error = ""
        for attempt in range(RETRY_TIMES):
            try:
                # 每次重试都更换请求头
                self.session.headers.update(get_random_headers())
                self.session.headers['Cookie'] = self.cookie
                # 随机延迟
                if attempt > 0:
                    delay = random.uniform(2 * attempt, 5 * attempt)
                    print(f"🔄 第{attempt+1}次重试，延迟{delay:.1f}秒...")
                    time.sleep(delay)
                return func(*args, **kwargs)
            except Exception as e:
                last_error = str(e)
                print(f"⚠️  第{attempt+1}次尝试失败: {last_error}")
                if attempt == RETRY_TIMES - 1:
                    return False, f"多次尝试失败: {last_error}"
        return False, last_error

    def daily_login(self):
        """每日登录 - 获取formhash和uid（增加重试）"""
        def _login():
            print("🔐 正在登录获取参数...")
            url = "https://www.right.com.cn/forum/forum.php"
            
            # 先发送一个预热请求
            try:
                self.session.get("https://www.right.com.cn", timeout=TIMEOUT)
                time.sleep(random.uniform(1, 3))
            except:
                pass

            response = self.session.get(url, timeout=TIMEOUT)
            print(f"🔍 登录响应状态码: {response.status_code}")

            if response.status_code == 200:
                # 检查是否需要重新登录（Cookie失效）
                if "登录" in response.text and "密码" in response.text:
                    return False, "Cookie已失效，请重新获取登录Cookie"
                
                # 提取formhash
                formhash_match = re.search(r'name="formhash"\s+value="([^"]+)"', response.text)
                if formhash_match:
                    self.formhash = formhash_match.group(1)
                    print(f"✅ 获取formhash成功: {self.formhash}")
                else:
                    return False, "未找到formhash参数"

                # 提取uid
                uid_match = re.search(r"discuz_uid\s*=\s*'(\d+)'", response.text)
                if uid_match:
                    self.uid = uid_match.group(1)
                    print(f"✅ 获取uid成功: {self.uid}")
                else:
                    return False, "未找到uid参数"

                return True, "登录成功"
            elif response.status_code == 521:
                return False, "521错误：服务器拒绝访问（可能是IP限制/反爬拦截）"
            else:
                return False, f"登录失败，状态码: {response.status_code}"

        return self._retry_request(_login)

    def get_user_info(self, is_after=False):
        """获取用户信息和积分（增加重试）"""
        def _get_info():
            print(f"👤 正在获取{'签到后' if is_after else '签到前'}用户信息...")
            time.sleep(random.uniform(2, 5))

            response = None
            last_status = None
            for url in CREDIT_URLS:
                for attempt in range(1, 3):
                    headers = {
                        **get_random_headers(),
                        'Referer': f'{BASE_URL}/forum.php',
                        'Cookie': self.cookie
                    }
                    try:
                        resp = self.session.get(
                            url=url, 
                            headers=headers, 
                            timeout=TIMEOUT,
                            allow_redirects=True
                        )
                        last_status = resp.status_code
                        if resp.status_code == 200 and resp.text:
                            response = resp
                            break
                        elif resp.status_code in (429, 521) or 500 <= resp.status_code < 600:
                            time.sleep(1.5 * attempt + random.uniform(0, 0.8))
                            continue
                        break
                    except:
                        continue
                if response is not None:
                    break

            if response is None:
                error_msg = f"获取用户信息失败，状态码: {last_status}"
                print(f"🔍 用户信息响应状态码: {last_status}")
                print(f"❌ {error_msg}")
                return False, error_msg

            print(f"🔍 用户信息响应状态码: {response.status_code}")

            if response.status_code == 200:
                # 提取积分信息
                coin = extract_first(
                    response.text,
                    patterns=[
                        r"恩山币\s*[:：]\s*</em>\s*([^<&\s]+)",
                        r"恩山币\s*[:：]\s*([^<\s]+)\s*币",
                        r"恩山币\s*[:：]\s*([^<\s]+)",
                    ],
                    default="0",
                    flags=re.S,
                )
                point = extract_first(
                    response.text,
                    patterns=[
                        r"积分\s*[:：]\s*</em>\s*([^<&\s]+)",
                        r"<em>\s*积分\s*[:：]\s*</em>\s*([^<\s]+)",
                        r"积分\s*[:：]\s*([^<\s]+)",
                    ],
                    default="0",
                    flags=re.S,
                )

                if is_after:
                    self.coin_after = coin
                    self.point_after = point
                    print(f"💰 签到后 - 恩山币: {coin}, 积分: {point}")
                else:
                    self.coin_before = coin
                    self.point_before = point
                    print(f"💰 签到前 - 恩山币: {coin}, 积分: {point}")

                # 只在第一次获取用户名等信息
                if not is_after:
                    self.user_name = extract_first(
                        response.text,
                        patterns=[
                            r'访问我的空间">([^<]+)</a>',
                            r'class="vwmy"[^>]*>([^<]+)</a>',
                            r'欢迎您回来\s*,\s*([^<\n]+)',
                            r'用户名[：:]\s*([^<\n]+)',
                        ],
                        default="未知用户",
                        flags=re.S,
                    )

                    self.user_group = extract_first(
                        response.text,
                        patterns=[
                            r'用户组\s*[:：]\s*([^<\n]+)</',
                            r'用户组\s*[:：]\s*([^<\n]+)',
                        ],
                        default="未知等级",
                        flags=re.S,
                    )

                    self.contribution = extract_first(
                        response.text,
                        patterns=[
                            r'贡献\s*[:：]\s*</em>\s*([^<\s]+)\s*分',
                            r'贡献\s*[:：]\s*(\d+)',
                        ],
                        default="0",
                        flags=re.S,
                    )

                    print(f"👤 用户: {mask_username(self.user_name)}")
                    print(f"🏅 等级: {self.user_group}")
                    print(f"🎯 贡献: {self.contribution}")

                return True, "用户信息获取成功"
            else:
                error_msg = f"获取用户信息失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                return False, error_msg

        return self._retry_request(_get_info)

    def perform_checkin(self):
        """执行签到（增加重试）"""
        def _checkin():
            print("📝 正在执行签到...")

            if not self.formhash:
                return False, "请先执行登录获取formhash"

            url = "https://www.right.com.cn/forum/plugin.php?id=erling_qd%3Aaction&action=sign"
            headers = {
                **get_random_headers(),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.right.com.cn",
                "Referer": "https://www.right.com.cn/forum/erling_qd-sign_in.html",
                "Cookie": self.cookie,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache"
            }

            data = f"formhash={self.formhash}"

            response = self.session.post(url, headers=headers, data=data, timeout=TIMEOUT)
            print(f"🔍 签到响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    if isinstance(result, dict):
                        if result.get('success') or '成功' in str(result.get('message', '')):
                            return True, result.get('message', '签到成功')
                        elif result.get('message'):
                            message = result['message']
                            if '已签到' in message or '已经签到' in message:
                                return True, message
                            else:
                                return False, f"签到失败: {message}"
                except ValueError:
                    return False, "响应格式错误，无法解析JSON"
            else:
                return False, f"签到请求失败，状态码: {response.status_code}"

        return self._retry_request(_checkin)

    def main(self):
        """主执行函数"""
        print(f"\n==== 恩山论坛账号{self.index} 开始签到 ====")

        if not self.cookie.strip():
            error_msg = """账号配置错误

❌ 错误原因: Cookie为空

🔧 解决方法:
1. 在青龙面板中添加环境变量enshan_cookie
2. 多账号用换行分隔或&&分隔
3. Cookie需要包含完整的登录信息

💡 提示: 请确保Cookie有效且格式正确"""
            print(f"❌ {error_msg}")
            return error_msg, False

        # 1. 获取签到前用户信息
        login_success, login_msg = self.daily_login()
        if not login_success:
            return f"登录失败: {login_msg}", False
        user_success, user_msg = self.get_user_info(is_after=False)
        if not user_success:
            print(f"⚠️ 获取用户信息失败: {user_msg}")

        # 2. 随机等待
        time.sleep(random.uniform(2, 5))

        # 3. 执行签到
        signin_success, signin_msg = self.perform_checkin()

        # 4. 获取签到后用户信息
        time.sleep(random.uniform(2, 4))
        after_success, after_msg = self.get_user_info(is_after=True)

        # 5. 通过积分变化判断签到是否真的成功
        gain_info = ""
        if after_success and self.coin_before and self.coin_after:
            try:
                coin_before = extract_number(self.coin_before)
                coin_after = extract_number(self.coin_after)
                point_before = extract_number(self.point_before)
                point_after = extract_number(self.point_after)

                coin_gain = coin_after - coin_before
                point_gain = point_after - point_before

                print(f"📊 积分变化: 恩山币 {coin_before}→{coin_after} (+{coin_gain}), 积分 {point_before}→{point_after} (+{point_gain})")

                if coin_gain > 0 or point_gain > 0:
                    signin_success = True
                    signin_msg = f"签到成功，获得 {coin_gain} 恩山币，{point_gain} 积分"
                    gain_info = f"\n🎁 本次收益: +{coin_gain} 恩山币, +{point_gain} 积分"
                    print(f"✅ 通过积分变化确认签到成功: +{coin_gain} 恩山币, +{point_gain} 积分")
                elif coin_gain == 0 and point_gain == 0:
                    signin_success = True
                    signin_msg = "今日已签到（积分无变化）"
                    print("📅 积分无变化，今日已签到")
                else:
                    print("⚠️ 积分变化异常，但仍认为签到成功")
                    signin_success = True

            except Exception as e:
                print(f"⚠️ 积分变化计算异常: {e}")
                print("🔄 使用原始签到结果")

        # 6. 组合结果消息
        final_msg = f"""🌟 恩山论坛签到结果

    👤 用户: {mask_username(self.user_name) or '未知用户'}
    🏅 等级: {self.user_group or '未知等级'}
    💰 恩山币: {self.coin_before or '未知'} → {self.coin_after or self.coin_before or '未知'}
    📊 积分: {self.point_before or '未知'} → {self.point_after or self.point_before or '未知'}
    🎯 贡献: {self.contribution or '0'} 分{gain_info}

    📝 签到: {signin_msg}
    ⏰ 时间: {datetime.now().strftime('%m-%d %H:%M')}"""

        print(f"{'✅ 任务完成' if signin_success else '❌ 任务失败'}")
        return final_msg, signin_success

def main():
    """主程序入口"""
    print(f"==== 恩山论坛签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")
    print(f"🔒 隐私保护模式: {'已启用' if privacy_mode else '已禁用'}")
    print(f"🔄 重试次数: {RETRY_TIMES}次")

    # 随机延迟（整体延迟）
    if random_signin:
        delay_seconds = random.randint(0, max_random_delay)
        if delay_seconds > 0:
            print(f"🎲 随机延迟: {format_time_remaining(delay_seconds)}")
            wait_with_countdown(delay_seconds, "恩山论坛签到")

    # 获取Cookie配置
    if not enshan_cookie:
        error_msg = """❌ 未找到enshan_cookie环境变量

🔧 配置方法:
1. enshan_cookie: 恩山论坛Cookie
2. 多账号用换行分隔或&&分隔
3. Cookie需要包含完整的登录信息

示例:
单账号: enshan_cookie=完整的Cookie字符串
多账号: enshan_cookie=cookie1&&cookie2 或换行分隔

💡 提示: 登录恩山论坛后，F12复制完整Cookie"""

        print(error_msg)
        notify_user("恩山论坛签到失败", error_msg)
        return

    cookies = parse_cookies(enshan_cookie)
    if not cookies:
        error_msg = """❌ Cookie解析失败

🔧 可能原因:
1. Cookie格式不正确
2. Cookie为空或只包含空白字符
3. 分隔符使用错误

💡 请检查enshan_cookie环境变量的值"""

        print(error_msg)
        notify_user("恩山论坛签到失败", error_msg)
        return

    print(f"📝 共发现 {len(cookies)} 个账号")

    success_count = 0
    total_count = len(cookies)
    results = []

    for index, cookie in enumerate(cookies):
        try:
            if index > 0:
                delay = random.uniform(10, 20)
                print(f"⏱️  随机等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)

            signer = EnShanSigner(cookie, index + 1)
            result_msg, is_success = signer.main()

            if is_success:
                success_count += 1

            results.append({
                'index': index + 1,
                'success': is_success,
                'message': result_msg,
                'username': mask_username(signer.user_name) if signer.user_name else f"账号{index + 1}"
            })

            status = "成功" if is_success else "失败"
            title = f"恩山论坛账号{index + 1}签到{status}"
            notify_user(title, result_msg)

        except Exception as e:
            error_msg = f"账号{index + 1}: 执行异常 - {str(e)}"
            print(f"❌ {error_msg}")
            notify_user(f"恩山论坛账号{index + 1}签到失败", error_msg)

    # 发送汇总通知
    if total_count > 1:
        summary_msg = f"""📊 恩山论坛签到汇总

📈 总计: {total_count}个账号
✅ 成功: {success_count}个
❌ 失败: {total_count - success_count}个
📊 成功率: {success_count/total_count*100:.1f}%
⏰ 完成时间: {datetime.now().strftime('%m-%d %H:%M')}"""

        if len(results) <= 5:
            summary_msg += "\n\n📋 详细结果:"
            for result in results:
                status_icon = "✅" if result['success'] else "❌"
                summary_msg += f"\n{status_icon} {result['username']}"

        notify_user("恩山论坛签到汇总", summary_msg)

    print(f"\n==== 恩山论坛签到完成 - 成功{success_count}/{total_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====")

def handler(event, context):
    """云函数入口"""
    main()

if __name__ == "__main__":
    main()
