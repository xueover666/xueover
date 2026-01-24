#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cron:1 0 * * *
# new Env("HIFI音乐签到")

"""
项目名称: Hifiti 自动签到 (Pro版)
脚本说明: 支持多账号、日志美化、结果聚合推送
环境变量: 
    HIFITI_DATA: 账号数据，格式为 "邮箱&密码"。
                 多账号请在青龙环境变量的值中换行，或新建多个同名变量。
"""

import requests
import hashlib
import os
import sys
import time
import json
import re

# 尝试导入推送模块
try:
    from notify import send
except ImportError:
    def send(title, content):
        print(f"\n【通知模拟】{title}\n{content}")

class HifitiSign:
    def __init__(self, index, email, password):
        self.index = index
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.hifiti.com',
            'Referer': 'https://www.hifiti.com/'
        }
        self.log_msg = "" # 用于存储单次运行的日志

    def log(self, content):
        """日志输出并累积"""
        print(content)
        self.log_msg += content + "\n"

    def mask_email(self, email):
        """邮箱脱敏显示"""
        if "@" in email:
            name, domain = email.split("@")
            if len(name) > 3:
                return f"{name[:2]}****{name[-1]}@{domain}"
            return f"{name}****@{domain}"
        return email

    def md5_encrypt(self, text):
        md5 = hashlib.md5()
        md5.update(text.encode('utf-8'))
        return md5.hexdigest()

    def login(self):
        login_page = "https://www.hifiti.com/user-login.htm"
        
        # 步骤 1: 预访问
        try:
            self.log(f"   Step 1: 🚀 初始化连接...")
            init_headers = self.headers.copy()
            if 'X-Requested-With' in init_headers: del init_headers['X-Requested-With']
            self.session.get(login_page, headers=init_headers)
            time.sleep(1)
        except Exception as e:
            self.log(f"   ⚠️ 初始化失败: {e}")
            return False

        # 步骤 2: 登录
        login_headers = self.headers.copy()
        login_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        login_headers['Referer'] = login_page
        
        payload = {
            "email": self.email,
            "password": self.md5_encrypt(self.password)
        }

        try:
            self.log(f"   Step 2: 🔑 正在验证身份...")
            res = self.session.post(login_page, headers=login_headers, data=payload)
            
            if res.status_code == 200 and ("0" in res.text or "成功" in res.text):
                # 步骤 3: 刷新 Token
                self.log(f"   Step 3: 🔄 刷新权限Token...")
                self.session.get('https://www.hifiti.com/', headers=self.headers)
                
                # 验证 Token 是否存在
                cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
                if 'bbs_token' in cookies:
                    return True
                else:
                    self.log("   ⚠️ 警告: 登录成功但未获取到 Token，尝试继续...")
                    return True
            else:
                self.log(f"   ❌ 登录失败: {res.text[:50]}")
                return False
        except Exception as e:
            self.log(f"   ❌ 登录异常: {e}")
            return False

    def sign_in(self):
        sign_url = "https://www.hifiti.com/sg_sign.htm"
        
        sign_headers = self.headers.copy()
        if 'Content-Type' in sign_headers: del sign_headers['Content-Type']
        
        try:
            self.log("   Step 4: 📝 发起签到请求...")
            time.sleep(1)
            res = self.session.post(sign_url, headers=sign_headers)
            
            if res.status_code == 200:
                try:
                    # 尝试解析 JSON
                    data = res.json()
                    msg = data.get("message", str(data))
                    code = data.get("code")
                    
                    if str(code) == "0" or "成功" in msg:
                        return f"✅ 签到成功: {msg}"
                    elif "已经" in msg:
                        return f"🔁 重复签到: {msg}"
                    elif "登录" in msg:
                        return f"❌ 签到失败: Cookie 失效"
                    else:
                        return f"⚠️ 未知状态: {msg}"
                except:
                    # 如果不是JSON，直接返回文本
                    if "已经" in res.text: return "🔁 今天已签到"
                    return f"✅ 操作完成: {res.text[:30]}"
            else:
                return f"❌ 请求错误: HTTP {res.status_code}"
                
        except Exception as e:
            return f"❌ 运行报错: {e}"

    def run(self):
        print(f"\n────── 👤 账号 {self.index}: {self.mask_email(self.email)} ──────")
        
        if self.login():
            result = self.sign_in()
        else:
            result = "❌ 登录步骤失败，跳过签到"
        
        self.log(f"   ➜ {result}")
        return f"账号{self.index}: {self.mask_email(self.email)}\n结果: {result}"

def get_env_accounts():
    """解析环境变量，支持多行和&符号"""
    if "HIFITI_DATA" not in os.environ:
        return []
    
    env_data = os.environ["HIFITI_DATA"]
    
    # 优先按换行符分割（青龙标准多账号格式）
    if '\n' in env_data:
        lines = env_data.split('\n')
    elif '&' in env_data and '@' in env_data:
        # 兼容处理: 有些人可能在一个变量里用 & 连接多个账号 user1&pwd1&user2&pwd2 (不推荐但防错)
        # 这里主要处理标准格式 user&pwd
        lines = [env_data]
    else:
        lines = [env_data]

    accounts = []
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 寻找账号密码分隔符，只分割第一个 &
        parts = line.split('&', 1)
        if len(parts) == 2:
            accounts.append((parts[0], parts[1]))
        else:
            print(f"⚠️ 格式错误跳过: {line} (请使用 邮箱&密码)")
            
    return accounts

if __name__ == "__main__":
    print("=" * 40)
    print("      Hifiti 论坛自动签到 Pro      ")
    print("=" * 40)

    account_list = get_env_accounts()
    
    if not account_list:
        print("❌ 未找到环境变量 HIFITI_DATA")
        print("👉 请在青龙面板添加变量，格式: 邮箱&密码")
        sys.exit(1)
        
    print(f"检测到 {len(account_list)} 个账号，开始工作...\n")
    
    notify_content = []
    
    for i, (email, pwd) in enumerate(account_list):
        # 实例化并运行
        bot = HifitiSign(i + 1, email, pwd)
        res_msg = bot.run()
        notify_content.append(res_msg)
        
        # 账号间随机延迟，防并发风控
        if i < len(account_list) - 1:
            wait_time = 3
            print(f"⏳ 等待 {wait_time} 秒切换下一个账号...")
            time.sleep(wait_time)

    # 发送汇总通知
    final_msg = "\n\n".join(notify_content)
    send("Hifiti 签到汇总", final_msg)
    
    print("\n" + "=" * 40)
    print("✅ 所有任务执行完毕")