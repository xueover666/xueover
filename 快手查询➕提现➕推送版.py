import requests
import json
import traceback
import os
import time
import random
from datetime import datetime, timedelta

# ==================== 功能开关配置 ====================
EXCHANGE_SWITCH = int(os.environ.get("EXCHANGE_SWITCH", "0"))  # 兑换功能开关: 1开启 0关闭
WITHDRAW_SWITCH = int(os.environ.get("WITHDRAW_SWITCH", "0"))  # 提现功能开关: 1开启 0关闭
WITHDRAW_AMOUNT = float(os.environ.get("WITHDRAW_AMOUNT", "0"))  # 提现金额配置: 0为自动匹配，否则使用指定金额
# ==================== WxPusher配置 ====================
WXPUSHER_SWITCH = int(os.environ.get("WXPUSHER_SWITCH", "1"))  # WxPusher通知开关: 1开启 0关闭
WXPUSHER_TOKEN = os.environ.get("WXPUSHER_TOKEN", "填你的")  # WxPusher的APP_TOKEN
WXPUSHER_TOPIC_IDS = os.environ.get("WXPUSHER_TOPIC_IDS", "填你的")  # 主题ID，多个用逗号分隔
WXPUSHER_UIDS = os.environ.get("WXPUSHER_UIDS", "填你的")  # 用户UID，多个用逗号分隔
# ====================================================

class Console:
    @staticmethod
    def _print(prefix: str, text: str):
        print(f"{prefix} {text}")

    @staticmethod
    def info(text: str):
        Console._print("  ", text)

    @staticmethod
    def success(text: str):
        Console._print("✅", text)

    @staticmethod
    def warn(text: str):
        Console._print("⚠️", text)

    @staticmethod
    def error(text: str):
        Console._print("❌", text)

    @staticmethod
    def step(text: str):
        Console._print("🎯", text)

class WxPusher:
    """WxPusher消息推送类"""
    
    @staticmethod
    def send_message(content: str, summary: str = "快手极速版通知"):
        """发送WxPusher消息"""
        if not WXPUSHER_SWITCH or not WXPUSHER_TOKEN:
            return False
            
        url = "https://wxpusher.zjiecode.com/api/send/message"
        
        # 构建接收人配置
        uids = []
        topic_ids = []
        
        if WXPUSHER_UIDS:
            uids = [uid.strip() for uid in WXPUSHER_UIDS.split(",") if uid.strip()]
        if WXPUSHER_TOPIC_IDS:
            topic_ids = [topic_id.strip() for topic_id in WXPUSHER_TOPIC_IDS.split(",") if topic_id.strip()]
            
        if not uids and not topic_ids:
            Console.warn("WxPusher未配置接收人")
            return False
        
        data = {
            "appToken": WXPUSHER_TOKEN,
            "content": content,
            "summary": summary,
            "contentType": 1,  # 1表示文字
            "topicIds": topic_ids,
            "uids": uids,
            "url": ""  # 可选链接
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 1000:
                Console.success("WxPusher通知发送成功")
                return True
            else:
                Console.warn(f"WxPusher通知发送失败: {result.get('msg')}")
                return False
        except Exception as e:
            Console.warn(f"WxPusher通知异常: {str(e)}")
            return False

class UA_Manager:
    """UA池管理器"""
    
    def __init__(self):
        self.ua_list = [
            # Android 设备 UA
            "Mozilla/5.0 (Linux; Android 12; SM-G991B Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 Mobile Safari/537.36 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            "Mozilla/5.0 (Linux; Android 13; 23117RK66C Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 KsWebView/1.8.121.885 (rel) Mobile Safari/537.36 Yoda/3.2.16-rc19 ksNebula/13.8.40.10657 OS_PRO_BIT/64 MAX_PHY_MEM/23116 KDT/PHONE AZPREFIX/az4",
            "Mozilla/5.0 (Linux; Android 11; M2012K11AC Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 Mobile Safari/537.36 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            "Mozilla/5.0 (Linux; Android 10; VOG-AL00 Build/HUAWEIVOG-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 Mobile Safari/537.36 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            "Mozilla/5.0 (Linux; Android 9; PCT-AL10 Build/HUAWEIPCT-AL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 Mobile Safari/537.36 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            # iOS 设备 UA
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KsWebView/1.8.121.885 (rel) Yoda/3.2.16-rc19 ksNebula/13.8.40.10657",
            # 原脚本的UA
            "Mozilla/5.0 (Linux; Android 16; 23117RK66C Build/BP2A.250605.031.A3; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.212 KsWebView/1.8.121.885 (rel) Mobile Safari/537.36 Yoda/3.2.16-rc19 ksNebula/13.8.40.10657 OS_PRO_BIT/64 MAX_PHY_MEM/23116 KDT/PHONE AZPREFIX/az4 ICFO/0 StatusHT/39 TitleHT/219 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/21.716 DPP/99 SHP/2254 SWP/1080 SD/2.625 CT/0 ISLM/0"
        ]
        
    def get_random_ua(self):
        """获取随机UA"""
        return random.choice(self.ua_list)
    
    def get_rotation_ua(self, index):
        """根据索引获取UA（轮询方式）"""
        return self.ua_list[index % len(self.ua_list)]

class KuaishouQuery:
    def __init__(self, cookie: str = None, remark: str = None, ua_index: int = 0):
        self.ua_manager = UA_Manager()
        self.user_agent = self.ua_manager.get_rotation_ua(ua_index)  # 使用轮询UA
        self.remark = remark
        self.session = requests.Session()  # 使用session保持连接
        # 设置连接池和超时
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100))
        
        if cookie is not None:
            parts = cookie.strip().split('#')
            if len(parts) >= 2:
                self.cookie = parts[1] if len(parts) >= 3 else parts[0]
            else:
                self.cookie = cookie.strip()
        else:
            ksck_env = os.environ.get("ksck")
            if ksck_env:
                parts = ksck_env.strip().split('#')
                if len(parts) >= 2:
                    self.cookie = parts[1] if len(parts) >= 3 else parts[0]
                else:
                    self.cookie = ksck_env.strip()
            else:
                Console.warn("未设置 cookie")
                self.cookie = ""
        
        if not self.cookie:
            Console.error("未找到有效的cookie")
            return

    def _make_request(self, url, method='GET', headers=None, params=None, data=None, json_data=None, retry_count=3):
        """统一的请求方法，支持重试和UA轮换"""
        for attempt in range(retry_count):
            try:
                # 每次请求都使用新的随机UA
                current_headers = headers.copy() if headers else {}
                current_headers['User-Agent'] = self.ua_manager.get_random_ua()
                
                if method.upper() == 'GET':
                    response = self.session.get(
                        url, 
                        headers=current_headers, 
                        params=params, 
                        timeout=(5, 10)  # 连接超时5s，读取超时10s
                    )
                elif method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        headers=current_headers, 
                        params=params, 
                        data=data,
                        json=json_data,
                        timeout=(5, 10)
                    )
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                return response
                
            except requests.exceptions.Timeout:
                Console.warn(f"请求超时，第{attempt + 1}次重试...")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                continue
                
            except requests.exceptions.ConnectionError:
                Console.warn(f"连接错误，第{attempt + 1}次重试...")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                Console.error(f"请求异常: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                continue
                
        return None

    def get_user_info(self):
        """获取用户信息（真实昵称）"""
        url = "https://nebula.kuaishou.com/rest/n/nebula/activity/earn/overview/basicInfo"
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/profit?layoutType=4&tab=coin&source=moneyMain&exchange_type=MANUAL",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": self.cookie
        }
        
        response = self._make_request(url, headers=headers)
        if not response:
            Console.error("获取用户信息请求失败")
            return None
            
        if response.status_code == 200:
            resp = response.json()
            if resp.get('result') == 1:
                user_data = resp.get('data', {}).get('userData', {})
                nickname = user_data.get('nickname')
                if nickname:
                    Console.success(f"用户昵称: [{nickname}]")
                    return nickname
                else:
                    Console.warn("未获取到用户昵称")
            else:
                Console.error(f"获取用户信息失败: {resp.get('error_msg', '未知错误')}")
        else:
            Console.error(f"获取用户信息HTTP失败: {response.status_code}")
        
        return None

    def get_account_overview(self):
        """获取账户概览信息"""
        Console.step("获取账户信息中...")
        url = "https://nebula.kuaishou.com/rest/n/nebula/account/overview"
        
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/profit?layoutType=4&tab=coin&source=moneyMain&exchange_type=MANUAL",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": self.cookie
        }
        
        response = self._make_request(url, headers=headers)
        if not response:
            Console.error("获取账户信息请求失败")
            return {'error': '请求失败', 'nickname': self.remark or '未知用户'}
            
        if response.status_code == 200:
            resp = response.json()
            
            if resp.get('result') == 1:
                data = resp.get('data', {})
                
                coin_balance = data.get('coinBalance', '0')
                cash_balance = data.get('cashBalance', '0')
                accumulative_amount = data.get('accumulativeAmount', '0')
                
                # 获取真实用户昵称
                nickname = self.get_user_info()
                if not nickname:
                    # 如果获取真实昵称失败，使用备注或从cookie中获取
                    nickname = self.remark
                    if not nickname:
                        cookie_lines = self.cookie.split(';')
                        for line in cookie_lines:
                            if 'userId=' in line:
                                nickname = line.split('userId=')[1].strip()
                                break
                        if not nickname:
                            nickname = "未知用户"
                
                # 用[]括起来显示昵称
                display_nickname = f"[{nickname}]"
                print(f"👤 用户{display_nickname} | 金币: {coin_balance} | 余额: {cash_balance}元")
                
                return {
                    'nickname': nickname,  # 存储原始昵称
                    'display_nickname': display_nickname,  # 存储带括号的显示昵称
                    'coin_balance': coin_balance,
                    'cash_balance': cash_balance,
                    'accumulative_amount': accumulative_amount,
                    'coin_records': data.get('coinAccountPage', {}).get('data', []),
                    'cash_records': data.get('cashAccountPage', {}).get('data', []),
                    'coin_cursor': data.get('coinAccountPage', {}).get('cursor'),
                    'coin_has_next': data.get('coinAccountPage', {}).get('hasNext', False)
                }
            else:
                error_msg = resp.get('error_msg', '未知错误')
                Console.error(f"接口返回错误: {error_msg}")
                return {'error': error_msg, 'nickname': self.remark or '未知用户', 'display_nickname': f"[{self.remark or '未知用户'}]"}
        else:
            Console.error(f"HTTP请求失败: {response.status_code}")
            return {'error': f'HTTP请求失败: {response.status_code}', 'nickname': self.remark or '未知用户', 'display_nickname': f"[{self.remark or '未知用户'}]"}

    def get_coin_history(self, cursor=None):
        """获取金币历史记录"""
        url = "https://nebula.kuaishou.com/rest/n/nebula/account/list"
        params = {
            "accountType": "coin",
            "cursor": cursor if cursor else ""
        }
        
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/profit?layoutType=4&tab=coin&source=moneyMain&exchange_type=MANUAL",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": self.cookie
        }
        
        response = self._make_request(url, headers=headers, params=params)
        if not response:
            return None
            
        if response.status_code == 200:
            resp = response.json()
            if resp.get('result') == 1:
                return resp.get('data', {})
            else:
                Console.error(f"获取记录失败: {resp.get('error_msg', '未知错误')}")
        else:
            Console.error(f"HTTP请求失败: {response.status_code}")
            
        return None

    def get_today_income(self, account_data):
        """获取今日收益"""
        if not account_data:
            return 0
            
        # 获取今日金币记录
        today = datetime.now().strftime("%Y.%m.%d")
        coin_records = account_data.get('coin_records', [])
        
        # 筛选今日记录
        today_records = [record for record in coin_records if record.get('createTime', '').startswith(today)]
        
        # 计算今日总收入（只计算正数）
        today_income = 0
        for record in today_records:
            amount = int(record.get('amount', 0))
            if amount > 0:
                today_income += amount
                
        return today_income

    def get_recent_coin_records(self, account_data, days=3):
        """获取最近指定天数的金币记录"""
        all_records = []
        target_date = (datetime.now() - timedelta(days=days-1)).strftime("%Y.%m.%d")
        
        # 使用传入的账户数据中的第一页记录
        if account_data and account_data.get('coin_records'):
            first_page_records = account_data['coin_records']
            # 筛选最近days天的记录
            filtered_records = [record for record in first_page_records 
                              if record.get('createTime', '') >= target_date]
            all_records.extend(filtered_records)
        
        # 获取后续页面，直到没有更多数据或记录日期早于目标日期
        cursor = account_data.get('coin_cursor') if account_data else None
        has_next = account_data.get('coin_has_next', False) if account_data else False
        
        total_pages = 1
        max_pages = 20  # 减少最大页数限制，提高速度
        
        while has_next and cursor and total_pages < max_pages:
            total_pages += 1
            page_data = self.get_coin_history(cursor)
            
            if not page_data:
                break
                
            records = page_data.get('data', [])
            if records:
                # 筛选最近days天的记录
                filtered_records = [record for record in records 
                                  if record.get('createTime', '') >= target_date]
                if filtered_records:
                    all_records.extend(filtered_records)
                
                # 如果本页有记录早于目标日期，说明已经获取完所有目标日期的记录
                if len(filtered_records) < len(records):
                    break
            else:
                break
                
            has_next = page_data.get('hasNext', False)
            cursor = page_data.get('cursor')
            
            time.sleep(0.2)  # 减少等待时间
        
        return all_records

    def analyze_detailed_income(self, account_data, days=3):
        """分析多日详细收益"""
        # 获取最近days天的金币记录
        recent_records = self.get_recent_coin_records(account_data, days)
        
        if not recent_records:
            Console.warn("无法获取交易记录")
            return 0  # 返回今日收益为0
        
        # 表情符号映射
        emoji_map = {
            '看视频额外奖励': '🎁',
            '看视频金币奖励': '📺', 
            '多天签到额外奖励': '📅',
            '开宝箱额外奖励': '🎰',
            '开宝箱奖励': '🎰',
            '看广告金币奖励': '👀',
            '饭补看广告金币奖励': '🍚',
            '搜索金币奖励': '🔍',
            '签到奖励': '📅',
            '金币兑换现金': '💸',
            '金币游乐园活动奖励': '🎡',
            '幸运刮刮刮中奖': '🎯',
            '购买幸运刮刮刮': '🎫',
            '其他': '💰'
        }
        
        # 按日期分组统计
        date_stats = {}
        for record in recent_records:
            date = record.get('createTime', '')
            event_type = record.get('eventType', '')
            amount = int(record.get('amount', 0))
            
            if date not in date_stats:
                date_stats[date] = {
                    'total': 0,
                    'categories': {},
                    'exchange_out': 0,
                    'record_count': 0
                }
            
            # 分类统计
            if event_type not in date_stats[date]['categories']:
                date_stats[date]['categories'][event_type] = 0
            date_stats[date]['categories'][event_type] += amount
            
            # 记录条数
            date_stats[date]['record_count'] += 1
            
            # 总收入（只计算正数）
            if amount > 0:
                date_stats[date]['total'] += amount
            elif '兑换' in event_type:
                date_stats[date]['exchange_out'] += abs(amount)
        
        # 输出最近几天的统计
        print("📊 最近3天收益详情")
        print("=" * 60)
        
        # 获取最近的日期
        sorted_dates = sorted(date_stats.keys(), reverse=True)[:days]
        
        # 计算三日趋势
        trend_data = {}
        if len(sorted_dates) >= 3:
            today_income = date_stats[sorted_dates[0]]['total'] if sorted_dates[0] in date_stats else 0
            yesterday_income = date_stats[sorted_dates[1]]['total'] if sorted_dates[1] in date_stats else 0
            day_before_income = date_stats[sorted_dates[2]]['total'] if sorted_dates[2] in date_stats else 0
            
            if yesterday_income > 0:
                trend_vs_yesterday = ((today_income - yesterday_income) / yesterday_income) * 100
            else:
                trend_vs_yesterday = 0
                
            if day_before_income > 0:
                trend_vs_day_before = ((today_income - day_before_income) / day_before_income) * 100
            else:
                trend_vs_day_before = 0
                
            trend_data = {
                'today': today_income,
                'yesterday': yesterday_income,
                'day_before': day_before_income,
                'vs_yesterday': trend_vs_yesterday,
                'vs_day_before': trend_vs_day_before
            }
        
        for date in sorted_dates:
            daily_data = date_stats[date]
            daily_income = daily_data['total']
            daily_exchange = daily_data['exchange_out']
            daily_records = daily_data['record_count']
            
            print(f"\n📅 {date} (共{daily_records}笔)")
            print(f"   💰 总收入: {daily_income:,} 金币")
            
            if daily_exchange > 0:
                print(f"   💸 兑换支出: -{daily_exchange:,} 金币")
            
            # 显示各分类收入
            sorted_categories = sorted(
                [(k, v) for k, v in daily_data['categories'].items() if v > 0],
                key=lambda x: x[1],
                reverse=True
            )[:6]  # 只显示前6个分类
            
            for event_type, amount in sorted_categories:
                emoji = emoji_map.get(event_type, '💰')
                percentage = (amount / daily_income) * 100 if daily_income > 0 else 0
                print(f"   {emoji} {event_type}: {amount:,} 金币 ({percentage:.1f}%)")
        
        # 输出三日趋势分析
        if trend_data:
            print("=" * 60)
            print("📈 三日趋势分析")
            print(f"   📊 较昨日: {'↑' if trend_data['vs_yesterday'] > 0 else '↓'} {abs(trend_data['vs_yesterday']):.1f}%")
            print(f"   📊 较前日: {'↑' if trend_data['vs_day_before'] > 0 else '↓'} {abs(trend_data['vs_day_before']):.1f}%")
            print("=" * 60)
            
        # 返回今日收益
        today_str = datetime.now().strftime("%Y.%m.%d")
        today_income = date_stats.get(today_str, {}).get('total', 0)
        return today_income

    def get_month_withdraw(self, account_data):
        """获取当月提现金额"""
        if not account_data:
            return 0.0
            
        cash_records = account_data.get('cash_records', [])
        
        # 统计当月提现总额
        current_month = datetime.now().strftime('%Y.%m')
        month_withdraw_total = 0.0
        
        for record in cash_records:
            create_time = record.get('createTime', '')
            event_type = record.get('eventType', '')
            if create_time.startswith(current_month) and '提现成功' in event_type:
                amount = float(record.get('amount', 0))
                if amount < 0:
                    month_withdraw_total += abs(amount)
        
        return month_withdraw_total

    def coinToCash(self, coin_amount: int):
        """金币兑换现金"""
        if not coin_amount or int(coin_amount) < 100:
            Console.warn("金币不足100，无法兑换")
            return False
            
        url = "https://nebula.kuaishou.com/rest/n/nebula/exchange/coinToCash/submit"
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/profit?layoutType=4&tab=cash&source=moneyMain&exchange_type=MANUAL",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": self.cookie
        }
        
        exchangeable = (int(coin_amount) // 100) * 100
        remainder = int(coin_amount) - exchangeable
        expected_cash_yuan = exchangeable / 10000.0
        
        Console.step(f"兑换: {exchangeable:,} 💰 → {expected_cash_yuan:.4f} 💵 (剩余: {remainder} 💰)")

        data = {"coinAmount": exchangeable, "token": "rE2zK-Cmc82uOzxMJW7LI2-wTGcKMqqAHE0PhfN0U4bJY4cAM5Inxw"}
        
        response = self._make_request(url, method='POST', headers=headers, json_data=data)
        if not response:
            Console.error("兑换请求失败")
            return False
            
        if response.status_code == 200:
            resp = response.json()
            if resp.get('result') == 1:
                Console.success("兑换成功")
                return True
            else:
                Console.error(f"兑换失败：{resp.get('error_msg', '未知错误')}")
        else:
            Console.error(f"兑换HTTP失败: {response.status_code}")
        
        return False

    def withdraw_query(self):
        """查询提现额度信息"""
        url = "https://nebula.kuaishou.com/rest/n/nebula/account/withdraw"
        headers = {
            "Connection": "keep-alive",
            "cookie": self.cookie,
        }
        
        response = self._make_request(url, headers=headers)
        if not response:
            return None
            
        if response.status_code == 200:
            resp = response.json()
            if resp.get('result') == 1:
                return resp
        else:
            Console.error(f"查询提现额度HTTP失败: {response.status_code}")
        return None

    def withdraw_info(self):
        """绑定信息查询，返回 provider 列表"""
        url = "https://www.kuaishoupay.com/pay/account/h5/withdraw/withdraw_info"
        headers = {
            "cookie": self.cookie,
        }
        data = {
            "account_group_key": "NEBULA_CASH_ACCOUNT",
            "providers": "",
            "bind_page_type": "3",
            "source": "COMMON_WITHDRAW_PAGE",
            "amount": "300"
        }
        
        response = self._make_request(url, method='POST', headers=headers, data=data)
        if not response:
            return [], ""
            
        if response.status_code == 200:
            resp = json.loads(response.text)
            if resp.get('code') == "SUCCESS":
                providers = resp.get("withdraw_provider_infos", [])
                ticket = resp.get("ticket", "")
                return providers, ticket
            else:
                Console.warn(resp.get("msg", response.text))
        else:
            Console.error(f"获取绑定信息HTTP失败: {response.status_code}")
        
        return [], ""

    def withdraw_apply(self, fen: str, biz_content, provider: str = "WECHAT", bank_id: str = "", bank_token: str = "", ticket: str = ""):
        """提现申请"""
        url = "https://www.kuaishoupay.com/pay/account/h5/withdraw/apply"
        headers = {
            "cookie": self.cookie,
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        if isinstance(biz_content, dict):
            biz_content_str = json.dumps(biz_content, ensure_ascii=False, separators=(",", ":"))
        else:
            biz_content_str = str(biz_content)

        data = {
            "account_group_key": "NEBULA_CASH_ACCOUNT",
            "mobile_code": "",
            "fen": fen,
            "provider": provider,
            "total_fen": fen,
            "commission_fen": "0",
            "third_account": provider,
            "attach": "",
            "biz_content": biz_content_str,
            "session_id": "",
            "bank_id": bank_id,
            "bank_token": bank_token,
            "skip_show_third_bind_info": "false",
            "agree_sign_policy": "false",
            "ticket": ticket
        }
        
        response = self._make_request(url, method='POST', headers=headers, data=data)
        if not response:
            return False
            
        if response.status_code == 200:
            resp = json.loads(response.text)
            if resp.get('code') == "SUCCESS":
                Console.success(f"{resp.get('msg', '提现成功')}")
                return True
            else:
                Console.error(f"提现失败：{resp.get('msg', response.text)}")
        else:
            Console.error(f"提现HTTP失败: {response.status_code}")
        
        return False

    def auto_withdraw(self, account_data):
        """自动提现"""
        if not account_data:
            return False
            
        cash_balance = float(account_data['cash_balance'])
        
        # 检查余额是否足够最低提现
        if cash_balance < 0.3:
            Console.warn(f"余额不足，无法提现")
            return False
        
        Console.success("开始提现流程...")
        
        # 查询提现额度信息
        withdraw_resp = self.withdraw_query()
        if not withdraw_resp:
            Console.error("查询提现额度失败")
            return False
            
        data = withdraw_resp.get("data", {})
        try:
            en_withdraw_amount = float(str(data.get("enWithdrawAmount", "0") or "0"))
            en_withdraw_list = [float(x) for x in data.get("enWithdrawList", [])]
            
            # 确定目标提现金额
            if WITHDRAW_AMOUNT > 0:
                # 使用配置的固定金额
                target_amount = WITHDRAW_AMOUNT
                if target_amount not in en_withdraw_list or target_amount > en_withdraw_amount:
                    Console.warn(f"配置金额 {target_amount} 元不可用或余额不足")
                    return False
                Console.success(f"🎯 使用配置金额提现 {target_amount} 元")
            else:
                # 自动匹配最高可用档位
                candidates = [x for x in en_withdraw_list if x <= en_withdraw_amount]
                if not candidates:
                    Console.warn("余额不足或无可提现档位")
                    return False
                target_amount = max(candidates)
                Console.success(f"🎯 自动匹配提现 {target_amount} 元")
            
            # 查找对应的提现档位信息
            withdraw_list = data.get("withdrawList", [])
            target_item = None
            for item in withdraw_list:
                try:
                    if float(str(item.get("amount", "0"))) == target_amount and not item.get("disabled", False):
                        target_item = item
                        break
                except Exception:
                    continue
                    
            if not target_item:
                Console.warn("未找到匹配的提现档位")
                return False
                
            biz_content_raw = target_item.get("bizContent")
            biz_content = biz_content_raw if isinstance(biz_content_raw, str) else (biz_content_raw or {})
            fen = str(int(round(target_amount * 100)))
            
        except Exception as e:
            Console.error(f"处理提现数据失败: {str(e)}")
            return False

        # 查询绑定信息
        providers, ticket = self.withdraw_info()
        if not providers:
            Console.error("绑定信息查询失败")
            return False
            
        provider_map = {p.get("provider"): p for p in providers}

        # 支付渠道优先级：微信 -> 支付宝 -> 银行卡
        priority = ["WECHAT", "ALIPAY", "UNION_PAY_BANK"]
        
        # 支付渠道图标映射
        provider_icon_map = {
            "WECHAT": "💚 微信",
            "ALIPAY": "💙 支付宝", 
            "UNION_PAY_BANK": "💳 银行卡"
        }

        for provider in priority:
            cfg = provider_map.get(provider)
            if not cfg:
                Console.warn(f"跳过：未返回渠道 {provider}")
                continue
                
            if not cfg.get("has_bind", False) and provider != "UNION_PAY_BANK":
                Console.warn(f"跳过：{provider} 未绑定")
                continue
                
            if provider == "UNION_PAY_BANK" and not cfg.get("has_bind", False):
                Console.warn("跳过：银行卡未绑定")
                continue

            bank_id = cfg.get("bank_bind_infos", [{}])[0].get("bank_id", "") if provider == "UNION_PAY_BANK" else ""
            bank_token = cfg.get("bank_bind_infos", [{}])[0].get("bank_token", "") if provider == "UNION_PAY_BANK" else ""
            
            provider_icon = provider_icon_map.get(provider, provider)
            
            Console.step(f"尝试通过 {provider_icon} 提现 {target_amount} 元...")
            
            # 执行提现
            if self.withdraw_apply(fen=fen, biz_content=biz_content, provider=provider, bank_id=bank_id, bank_token=bank_token, ticket=ticket):
                Console.success(f"🎊 {provider_icon} 提现成功")
                return True
            else:
                Console.warn(f"{provider_icon} 提现失败，尝试下一个渠道...")

        Console.error("❌ 所有可用渠道均提现失败或未绑定")
        return False

    def auto_exchange_coins(self, account_data):
        """自动兑换金币"""
        if not account_data:
            return False
            
        coin_balance = int(account_data['coin_balance'])
        
        if coin_balance >= 100:
            Console.success("开始兑换金币...")
            if self.coinToCash(coin_balance):
                return True
            else:
                Console.error("兑换金币失败")
                return False
        else:
            Console.warn("金币不足100，无法兑换")
            return False

def print_centered_title(text):
    """打印居中标题"""
    total_width = 45
    text_width = len(text)
    side_width = (total_width - text_width) // 2
    left_side = "=" * side_width
    right_side = "=" * (total_width - text_width - side_width)
    print(f"{left_side}{text}{right_side}")

def main():
    # 打印居中标题
    print_centered_title("快手极速版查询兑换脚本")
    print(f"🚀兑换功能: {'✅ 开启' if EXCHANGE_SWITCH else '❌ 关闭'}")
    print(f"🚀提现功能: {'✅ 开启' if WITHDRAW_SWITCH else '❌ 关闭'}")
    print(f"🚀提现金额: {'💰 自动匹配最高档位' if WITHDRAW_AMOUNT == 0 else f'💰 固定金额 {WITHDRAW_AMOUNT} 元'}")
    print(f"🚀WxPusher通知: {'✅ 开启' if WXPUSHER_SWITCH else '❌ 关闭'}")
    print("🚀使用的python依赖有：requests")
    print("🚀Cookie变量名称：ksck 或 ksck1 到 ksck666")
    print("🚀支持备注昵称格式：备注#cookie#salt")
    print("⚠️ 本脚本仅供交流学习，请勿用于商业用途\n")

    ksck_env = os.environ.get("ksck", "") or ""
    
    # 处理多账号，支持备注昵称
    accounts = []
    
    if ksck_env:
        entries = ksck_env.split("&")
        for entry in entries:
            if entry.strip():
                parts = entry.strip().split('#')
                if len(parts) >= 3:
                    # 格式：备注#cookie#salt
                    remark = parts[0]
                    cookie_part = parts[1]
                    accounts.append({"cookie": cookie_part, "remark": remark})
                elif len(parts) == 2:
                    # 格式：cookie#salt
                    cookie_part = parts[0]
                    accounts.append({"cookie": cookie_part, "remark": None})
                else:
                    # 格式：cookie
                    accounts.append({"cookie": entry.strip(), "remark": None})
    
    # 处理 ksck1 到 ksck666 环境变量
    for i in range(1, 667):
        ksck_n = os.environ.get(f"ksck{i}")
        if ksck_n:
            parts = ksck_n.strip().split('#')
            if len(parts) >= 3:
                remark = parts[0]
                cookie_part = parts[1]
                accounts.append({"cookie": cookie_part, "remark": remark})
            elif len(parts) == 2:
                cookie_part = parts[0]
                accounts.append({"cookie": cookie_part, "remark": None})
            else:
                accounts.append({"cookie": ksck_n.strip(), "remark": None})

    # 用于统计总提现金额和通知内容
    total_month_withdraw = 0.0
    total_today_income = 0
    success_count = 0
    notification_content = "📊 快手极速版执行报告\n\n"
    start_time = datetime.now()

    if accounts:
        for idx, account_info in enumerate(accounts, start=1):
            # 居中的账号标题
            title_text = f"📋 账号 {idx}/{len(accounts)}"
            print_centered_title(title_text)
            
            query = KuaishouQuery(
                cookie=account_info["cookie"], 
                remark=account_info["remark"],
                ua_index=idx  # 为每个账号分配不同的UA索引
            )
            
            # 获取账户概览
            account_data = query.get_account_overview()
            
            if account_data and 'error' not in account_data:
                success_count += 1
                
                # 获取今日收益和当月提现
                month_withdraw = query.get_month_withdraw(account_data)
                today_income = query.analyze_detailed_income(account_data, days=3)
                
                # 累加到总计
                if month_withdraw:
                    total_month_withdraw += month_withdraw
                if today_income:
                    total_today_income += today_income
                
                # 自动兑换金币
                exchange_result = False
                if EXCHANGE_SWITCH:
                    exchange_result = query.auto_exchange_coins(account_data)
                
                # 自动提现
                withdraw_result = False
                if WITHDRAW_SWITCH:
                    withdraw_result = query.auto_withdraw(account_data)
                
                # 显示收益统计
                print("📋 收益统计")
                print(f"💰 今日收益: {today_income:,} 金币 ({today_income/10000:.2f}元)")
                print(f"💰 当月提现: {month_withdraw:.2f} 💵")
                print(f"💰 累计: {account_data.get('accumulative_amount', '0')} 💵\n")
                
                # 添加到通知内容 - 使用带括号的显示昵称
                notification_content += f"👤 {account_data['display_nickname']}\n"
                notification_content += f"   💰 金币: {account_data['coin_balance']}\n"
                notification_content += f"   💵 余额: {account_data['cash_balance']}元\n"
                notification_content += f"   📅 今日收益: {today_income:,} 金币 ({today_income/10000:.2f}元)\n"
                notification_content += f"   💸 当月提现: {month_withdraw:.2f}元\n"
                notification_content += f"   📈 累计: {account_data.get('accumulative_amount', '0')}元\n"
                if exchange_result:
                    notification_content += "   🔄 兑换: ✅成功\n"
                if withdraw_result:
                    notification_content += "   💸 提现: ✅成功\n"
                notification_content += "\n"
            else:
                error_msg = account_data.get('error', '未知错误') if account_data else '获取账户信息失败'
                Console.error(f"账号处理失败: {error_msg}")
                # 使用带括号的显示昵称
                display_nickname = account_data.get('display_nickname', f"[{account_info.get('remark', '未知用户')}]") if account_data else f"[{account_info.get('remark', '未知用户')}]"
                notification_content += f"👤 {display_nickname}\n"
                notification_content += f"   ❌ 失败: {error_msg}\n\n"
            
            if idx < len(accounts):
                time.sleep(random.randint(2, 4))  # 减少账号间等待时间
    else:
        Console.warn("未找到任何账号（ksck 或 ksck1 到 ksck666）")
        query = KuaishouQuery()
        account_data = query.get_account_overview()
        if account_data and 'error' not in account_data:
            success_count += 1
            
            # 获取今日收益和当月提现
            month_withdraw = query.get_month_withdraw(account_data)
            today_income = query.analyze_detailed_income(account_data, days=3)
            
            # 累加到总计
            if month_withdraw:
                total_month_withdraw += month_withdraw
            if today_income:
                total_today_income += today_income
            
            # 自动兑换金币
            exchange_result = False
            if EXCHANGE_SWITCH:
                exchange_result = query.auto_exchange_coins(account_data)
            
            # 自动提现
            withdraw_result = False
            if WITHDRAW_SWITCH:
                withdraw_result = query.auto_withdraw(account_data)
            
            # 显示收益统计
            print("📋 收益统计")
            print(f"💰 今日收益: {today_income:,} 金币 ({today_income/10000:.2f}元)")
            print(f"💰 当月提现: {month_withdraw:.2f} 💵")
            print(f"💰 累计: {account_data.get('accumulative_amount', '0')} 💵\n")
            
            # 添加到通知内容 - 使用带括号的显示昵称
            notification_content += f"👤 {account_data['display_nickname']}\n"
            notification_content += f"   💰 金币: {account_data['coin_balance']}\n"
            notification_content += f"   💵 余额: {account_data['cash_balance']}元\n"
            notification_content += f"   📅 今日收益: {today_income:,} 金币 ({today_income/10000:.2f}元)\n"
            notification_content += f"   💸 当月提现: {month_withdraw:.2f}元\n"
            notification_content += f"   📈 累计: {account_data.get('accumulative_amount', '0')}元\n"
            if exchange_result:
                notification_content += "   🔄 兑换: ✅成功\n"
            if withdraw_result:
                notification_content += "   💸 提现: ✅成功\n"

    # 汇总统计
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("📋 汇总统计")
    print(f"👤 账号总数: {len(accounts) if accounts else 1}")
    print(f"👤 成功处理: {success_count}")
    print(f"💰 今日总收益: {total_today_income:,} 金币 ({total_today_income/10000:.2f}元)")
    print(f"💰 当月总提现: {total_month_withdraw:.2f} 💵")
    print(f"⏱️ 执行耗时: {duration:.2f}秒\n")
    
    print("✅统计完成")

    # 发送WxPusher通知
    if WXPUSHER_SWITCH:
        summary_content = f"快手极速版 - 成功: {success_count}/{len(accounts) if accounts else 1} | 今日收益: {total_today_income/10000:.2f}元 | 总提现: {total_month_withdraw:.2f}元"
        notification_content += f"\n📊 汇总统计\n"
        notification_content += f"👤 账号总数: {len(accounts) if accounts else 1}\n"
        notification_content += f"✅ 成功处理: {success_count}\n"
        notification_content += f"💰 今日总收益: {total_today_income:,} 金币 ({total_today_income/10000:.2f}元)\n"
        notification_content += f"💸 当月总提现: {total_month_withdraw:.2f}元\n"
        notification_content += f"⏱️ 执行耗时: {duration:.2f}秒"
        
        WxPusher.send_message(notification_content, summary_content)

if __name__ == '__main__':
    main()