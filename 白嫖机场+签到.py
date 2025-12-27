# 当前脚本来自于 http://script.345yun.cn 脚本库下载！
# 脚本库官方QQ群: 429274456
# 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# 您在使用脚本库下载的脚本时自行检查判断风险。
# 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

'''
机场签到脚本 ✈️
每日签到获得免费流量 📊
邀请链接：https://i2a4b0e5c3.skyxcloud.icu/auth/register?code=Z0BrQK
通过邀请链接注册，可以获得30天免费会员 🎁
最低套餐每月仅需要0.5元，可自动续费 💰
'''

import requests
import time
import random
import re
import os

class SkyVpn():
    def __init__(self,user,password):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.TARGET_URL = "https://o1y54488p6.skyxcloud.icu/auth/login"
        self.CPK = "ge_ua_p"
        self.NONCE = None
        self.STEP = "prev"
        self.session.headers.update({
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://o1y54488p6.skyxcloud.icu",
            "referer": "https://o1y54488p6.skyxcloud.icu/auth/login",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        })
    def bypass_ua_check(self):
        print("🔍 正在绕过UA检测...")
        response = self.session.get(self.TARGET_URL)
        if response.status_code != 200:
            print("❌ UA检测失败，返回状态码:", response.status_code)
            return 369
        print("✅ 浏览器验证页面获取成功 🌐")
        ge_ua_p = self.session.cookies.get(self.CPK)
        if not ge_ua_p:
            print("⏰ 浏览器验证还在有效期内")
            return None
        nonce_match = re.search(r'var nonce = (\d+);', response.text)
        if nonce_match:
            self.NONCE = int(nonce_match.group(1))
            print(f"🔢 成功提取nonce值: {self.NONCE}")
        else:
            print("⚠️  未提取到 nonce 值")
            return None
        print(f"🔑 获取到有效的ge_ua_p值: {ge_ua_p}")
        print("🧮 正在计算 sum 参数...")
        sum_val = 0
        for i in range(len(ge_ua_p)):
            char = ge_ua_p[i]
            # 仅匹配字母/数字（JS 中 /^[a-zA-Z0-9]$/.test(r)）
            if re.match(r'^[a-zA-Z0-9]$', char):
                sum_val += ord(char) * (self.NONCE + i)
        print(f"✅ 计算得到 sum: {sum_val}")
        print("📤 正在发送验证POST请求...")
        post_headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "X-GE-UA-Step": self.STEP,
            "Referer": self.TARGET_URL  # 必要，避免跨域检测
        }
        post_data = {
            "sum": sum_val,
            "nonce": self.NONCE
        }
        # 发送 POST 请求（URL 与当前页面一致）
        post_response = self.session.post(self.TARGET_URL, data=post_data, headers=post_headers)
        if post_response.status_code != 200:
            print(f"❌ POST验证失败，状态码：{post_response.status_code}")
            return None
        print("✅ POST验证成功 🎉")

        print("⏳ 等待验证并刷新页面...")
        time.sleep(5)  # 对应 JS 中的 5 秒倒计时
        final_response = self.session.get(self.TARGET_URL)
        print(f"🔄 最终页面状态码：{final_response.status_code}")
        # print(f"最终页面内容：\n{final_response.text[:1000]}")  # 打印前 1000 字符

        return self.session, final_response      
    def get_auth_code(self):
        if self.bypass_ua_check() == 369:
            print("❌ UA校验失败,请检查网络连接")
            return
        print("🔐 正在获取授权码...")
        time.sleep(2)
        url = "https://o1y54488p6.skyxcloud.icu/user/authcode"
        response = self.session.post(url, headers=self.session.headers)
        if response.status_code == 200:
            # print(f"获取 authcode 成功：{response.cookies.get("server_name_session")}")
            self.session.cookies.set("server_name_session", response.cookies.get("server_name_session"))
            print("✅ 授权码获取成功 🎫")
        else:
            print(f"❌ 获取授权码失败，状态码：{response.status_code}")
            return
        
    def sign_in(self):
        time.sleep(2)
        url = "https://o1y54488p6.skyxcloud.icu/auth/login"
        data = {
            "email": self.user,
            "passwd": self.password,
            "remember_me": "on",
            "code": ""
        }
        response = self.session.post(url, data=data)
        if response.status_code == 200:
            cookie_str = "; ".join([f"{c.name}={c.value}" for c in response.cookies])
            if cookie_str:
                self.session.headers["Cookie"] = cookie_str
            res = response.json().get("msg")
            print(f"✅ 登录结果：{res}")
            time.sleep(random.uniform(3, 5))
            self.check_in()
        else:
            print(f"❌ 登录失败，状态码：{response.status_code}")
            return 
        
    def check_in(self):
        time.sleep(2)
        print("📅 正在签到...")
        url = "https://i2a4b0e5c3.skyxcloud.icu/user/checkin"
        response = self.session.post(url)
        if response.status_code == 200:
            res = response.json().get("msg")
            print(f"✅ 签到结果：{res}")
            total = response.json().get("traffic")
            
            if total:
                print(f"🎁 签到获得流量：{total}")
        else:
            print(f"❌ 签到失败，状态码：{response.status_code}")
            return 
    def user_info(self):
        time.sleep(2)
        print("👤 正在获取用户信息...")
        url = "https://o1y54488p6.skyxcloud.icu/user"
        response = self.session.get(url)
        if response.status_code != 200:
            print(f"❌ 获取用户信息失败，状态码：{response.status_code}")
            return
        content = response.text
        member_info = re.search(r'<span class="counter">(\d+)</span>\s+(\w+)', content, re.DOTALL)
        if member_info:
            print(f"⏰ 会员剩余时长: {member_info.group(1)}{member_info.group(2)}")
        else:
            print(f"⏰ 会员剩余时长: 未找到")

        vip_info = re.search(r'([^\s]+会员)\s*[:：]\s*(\d{4}-\d{2}-\d{2})\s*到期', content, re.DOTALL)
        if vip_info:

            print(f"👑 会员类型: {vip_info.group(1)}")
            print(f"📅 到期时间: {vip_info.group(2)}")
        else:
            print(f"👑 会员类型: 未找到")
            print(f"📅 到期时间: 未找到")
        traffic = re.findall(r'{ y: (\d+\.\d+), name:"([^"]+)",.*?legendText: "([^"]+)"', content, re.DOTALL)
        traffic_info = {}
        for match in traffic:
            traffic_value = float(match[0])  # 数值（3.13/0.03/38.63）
            traffic_name = re.sub(r'\(GB\)', '', match[1]).strip()  # 名称（已用/今日已用/剩余）
            traffic_info[traffic_name] = f"{traffic_value}GB"        
        
        if traffic_info:
            print("📊 流量信息:")
            for name, value in traffic_info.items():
                print(f"  📈 {name}: {value}")

        
def main():
    print("🚀 SkyVPN机场签到脚本启动!")
    account = os.getenv('skyvpn')
    if not account:
        print('⚠️  请设置环境变量：skyvpn 格式：注册邮箱#密码')
        print('🔗 邀请链接：https://i2a4b0e5c3.skyxcloud.icu/auth/register?code=Z0BrQK')
        print('🎁 通过邀请链接注册，可以获得30天免费会员')
        return
    print(f"👤 检测到可用账号")
    user, password = account.split('#')
    vpn = SkyVpn(user,password)
    print("🔓 开始获取授权码...")
    vpn.get_auth_code()
    print("🔑 开始登录...")
    vpn.sign_in()
    print("📊 开始获取用户信息...")
    vpn.user_info()
    print("✨ 脚本执行完成!")
    
if __name__ == "__main__":
    
    main()