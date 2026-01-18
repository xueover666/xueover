"""
//🐔场链接：https://freegangkou.top/#/register?code=IvBSG3iR
// 环境变量配置（环境变量名yjy（格式：QlaiEpEyu2qYfew0WHAXnq*****）
//抓headers里的authorization不要带Bearer
"""

# 导入需要的库
import requests
import time
from datetime import datetime

# authorization值
authorization = ''
# 优惠券代码和套餐ID（可根据需要修改）
COUPON_CODE = "muKnJjwV"
# 订阅1
PLAN_ID = "1"
# 循环执行次数, 自行修改次数
LOOP_TIMES = 10
# 每次循环间隔时间（秒），避免请求过快被限制
LOOP_INTERVAL = 1

# ======================== 基础配置 ========================
# 请求头配置，包含身份验证和浏览器信息
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "authorization": f"Bearer {authorization}",
    "content-language": "zh-CN",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://freegangkou.top",
    "priority": "u=1, i",
    "referer": "https://freegangkou.top/",
    "sec-ch-ua": "\"Chromium\";v=\"136\", \"Microsoft Edge\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
}

def execute_order_process(loop_index):
    """
    执行单次订单处理流程
    :param loop_index: 当前循环索引（从1开始）
    :return: bool - 是否执行成功
    """
    print(f"\n{'='*20} 开始执行第 {loop_index} 次循环 {'='*20}")
    
    try:
        # ======================== 第一步：检查优惠券 ========================
        print(f"\n[{loop_index}] 检查优惠券 {COUPON_CODE}")
        check_coupon_url = "https://freegangkou.top/api/v1/user/coupon/check"
        check_coupon_data = {
            "code": COUPON_CODE,
            "plan_id": PLAN_ID
        }
        
        coupon_response = requests.post(check_coupon_url, headers=headers, data=check_coupon_data)
        coupon_result = coupon_response.json()
        
        if coupon_result.get("status") != "success":
            print(f"[{loop_index}] 优惠券无效！错误信息：{coupon_result.get('message')}")
            return False
        
        print(f"[{loop_index}] 优惠券有效")

        # ======================== 第二步：提交订单 ========================
        print(f"\n[{loop_index}] 提交订单")
        create_order_url = "https://freegangkou.top/api/v1/user/order/save"
        create_order_data = {
            "plan_id": PLAN_ID,
            "period": "month_price",
            "coupon_code": COUPON_CODE
        }
        
        order_response = requests.post(create_order_url, headers=headers, data=create_order_data)
        order_result = order_response.json()
        
        if order_result.get("status") != "success":
            print(f"[{loop_index}] 订单创建失败！错误信息：{order_result.get('message')}")
            return False
        
        trade_no = order_result.get("data")
        print(f"[{loop_index}] 订单创建成功，订单号：{trade_no}")

        # ======================== 第三步：提交结算 ========================
        print(f"\n[{loop_index}] 提交结算")
        checkout_url = "https://freegangkou.top/api/v1/user/order/checkout"
        checkout_data = {
            "trade_no": trade_no,
            "method": "1"
        }
        
        checkout_response = requests.post(checkout_url, headers=headers, data=checkout_data)
        checkout_result = checkout_response.json()
        
        if checkout_result.get("data") is not True:
            print(f"[{loop_index}] 订单结算失败！返回信息：{checkout_result}")
            return False
        
        print(f"[{loop_index}] 订单结算成功")

        # ======================== 第四步：查询订单详情 ========================
        print(f"\n[{loop_index}] 查询订单详情")
        order_detail_url = "https://freegangkou.top/api/v1/user/order/detail"
        order_detail_params = {
            "trade_no": trade_no,
            "t": str(int(time.time() * 1000))
        }
        
        detail_response = requests.get(order_detail_url, headers=headers, params=order_detail_params)
        detail_result = detail_response.json()
        
        if detail_result.get("status") != "success":
            print(f"[{loop_index}] 查询订单失败！错误信息：{detail_result.get('message')}")
            return False
        
        order_info = detail_result.get("data")
        print(f"[{loop_index}] 订单状态：{order_info.get('status')} (3=已支付)")
        print(f"[{loop_index}] 套餐名称：{order_info.get('plan', {}).get('name')}")

        # ======================== 第五步：查询用户信息并计算剩余天数 ========================
        print(f"\n[{loop_index}] 查询用户信息并计算剩余天数")
        user_info_url = "https://freegangkou.top/api/v1/user/info"
        user_info_params = {
            "t": str(int(time.time() * 1000))
        }
        
        user_response = requests.get(user_info_url, headers=headers, params=user_info_params)
        user_result = user_response.json()
        
        if user_result.get("status") == "success":
            user_data = user_result.get("data")
            expired_at = user_data.get("expired_at")
            created_at = user_data.get("created_at")
            
            # 计算剩余天数
            remaining_seconds = expired_at - time.time()
            remaining_days = round(remaining_seconds / 86400, 2)
            
            # 格式化时间显示
            expired_datetime = datetime.fromtimestamp(expired_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{loop_index}] 账号过期时间：{expired_datetime}")
            print(f"[{loop_index}] 剩余使用天数：{remaining_days} 天")
        
        print(f"\n[{loop_index}] 第 {loop_index} 次循环执行完成 ✅")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n[{loop_index}] 网络请求出错：{e} ❌")
        return False
    except Exception as e:
        print(f"\n[{loop_index}] 程序执行出错：{e} ❌")
        return False

def main():
    """
    主函数：循环执行指定次数的订单处理流程
    """
    print(f"开始执行循环任务，总共执行 {LOOP_TIMES} 次")
    print(f"每次循环间隔 {LOOP_INTERVAL} 秒\n")
    
    # 记录成功和失败次数
    success_count = 0
    fail_count = 0
    
    # 循环执行
    for i in range(1, LOOP_TIMES + 1):
        # 执行单次流程
        is_success = execute_order_process(i)
        
        # 更新计数
        if is_success:
            success_count += 1
        else:
            fail_count += 1
        
        # 如果不是最后一次循环，添加间隔
        if i < LOOP_TIMES:
            print(f"\n[{i}] 等待 {LOOP_INTERVAL} 秒后执行下一次循环...")
            time.sleep(LOOP_INTERVAL)
    
    # 输出最终统计结果
    print(f"\n{'='*50}")
    print(f"循环执行完成！总计：{LOOP_TIMES} 次")
    print(f"成功：{success_count} 次")
    print(f"失败：{fail_count} 次")
    print(f"{'='*50}")

# 程序入口
if __name__ == "__main__":
    main()
