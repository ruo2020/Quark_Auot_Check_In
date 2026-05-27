#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
import urllib.parse

# ======================
# Telegram 通知
# ======================
def tg_send(message: str):
    """
    Telegram 纯文本通知（不使用 HTML / Markdown）
    """
    bot_token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not bot_token or not chat_id:
        print("⚠️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 TG 推送")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message[:4000],  # Telegram 单条限制保护
        "parse_mode": None       # 强制纯文本
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.ok:
            print("❌ Telegram 推送失败:", r.text)
    except Exception as e:
        print("❌ Telegram 推送异常:", e)


# ======================
# 通知入口（终端 + TG）
# ======================
def send(title, message):
    full_msg = f"{title}\n\n{message}"
    print(full_msg)
    tg_send(full_msg)


# ======================
# 环境变量读取
# ======================
def get_env():
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        send("夸克自动签到", "❌ 未添加 COOKIE_QUARK 变量")
        sys.exit(0)

    return [c.strip() for c in cookie_list if c.strip()]


# ======================
# 夸克签到类
# ======================
class Quark:
    def __init__(self, user_data):
        self.param = user_data

    def convert_bytes(self, b):
        units = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        r = requests.get(url=url, params=querystring).json()
        return r.get("data")

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode")
        }
        data = {"sign_cyclic": True}
        r = requests.post(url=url, json=data, params=querystring).json()
        if r.get("data"):
            return True, r["data"]["sign_daily_reward"]
        return False, r.get("message", "签到失败")

    def do_sign(self):
        log = ""
        info = self.get_growth_info()

        if not info:
            return f"❌ {self.param.get('user')} 获取成长信息失败\n"

        log += (
            f" {'88VIP' if info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
            f"💾 网盘总容量：{self.convert_bytes(info['total_capacity'])}，"
            f"签到累计容量："
        )

        if "sign_reward" in info['cap_composition']:
            log += f"{self.convert_bytes(info['cap_composition']['sign_reward'])}\n"
        else:
            log += "0 MB\n"

        if info["cap_sign"]["sign_daily"]:
            log += (
                f"✅ 今日已签到 +{self.convert_bytes(info['cap_sign']['sign_daily_reward'])}，"
                f"连签进度({info['cap_sign']['sign_progress']}/{info['cap_sign']['sign_target']})\n"
            )
        else:
            sign, reward = self.get_growth_sign()
            if sign:
                log += (
                    f"✅ 执行签到 +{self.convert_bytes(reward)}，"
                    f"连签进度({info['cap_sign']['sign_progress'] + 1}/{info['cap_sign']['sign_target']})\n"
                )
            else:
                log += f"❌ 签到异常: {reward}\n"

        return log


# ======================
# 主函数
# ======================
def main():
    msg = ""
    cookies = get_env()
    print(f"✅ 检测到共 {len(cookies)} 个夸克账号\n")

    for idx, ck in enumerate(cookies, start=1):
        user_data = {}
        for item in ck.replace(" ", "").split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                user_data[k] = v

        msg += f"🙍🏻♂️ 第 {idx} 个账号\n"
        msg += Quark(user_data).do_sign() + "\n"

    send("夸克自动签到", msg.strip())


# ======================
# 入口
# ======================
if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
