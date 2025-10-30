from __future__ import annotations

import time
import datetime as dt
from typing import Any, Dict, List, Optional
import requests
import urllib3
import certifi

# 關閉 SSL 警告（避免噪音，但仍會使用 certifi 驗證）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

T86_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"
BFI82U_URL = "https://www.twse.com.tw/rwd/zh/fund/BFI82U"

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": _UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Referer": "https://www.twse.com.tw/",
    })
    return s

def _yyyymmdd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")

def _iso_date(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")

def _safe_get(session: requests.Session, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
    """
    嘗試以 certifi 驗證憑證；若驗證失敗，改用 verify=False。
    """
    try:
        return session.get(url, params=params, timeout=20, verify=certifi.where())
    except requests.exceptions.SSLError:
        print("⚠️ SSL 憑證驗證失敗，改用非驗證連線（verify=False）")
        return session.get(url, params=params, timeout=20, verify=False)

def fetch_t86(date: dt.date, retry: int = 3, sleep_s: float = 0.6) -> List[Dict[str, Any]]:
    """
    Fetch T86 (三大法人買賣超日報表) for the given date.
    """
    params = {
        "response": "json",
        "date": _yyyymmdd(date),
        "selectType": "ALL",
    }
    s = _session()
    for _ in range(retry):
        r = _safe_get(s, T86_URL, params)
        if not r:
            continue
        if r.ok:
            js = r.json()
            if js.get("stat") == "OK" and js.get("data"):
                fields: List[str] = js.get("fields", [])
                rows: List[List[Any]] = js.get("data", [])
                docs: List[Dict[str, Any]] = []
                for row in rows:
                    m = {fields[idx]: row[idx] for idx in range(min(len(fields), len(row)))}
                    stock_code = m.get("證券代號") or m.get("股票代號")
                    stock_name = m.get("證券名稱") or m.get("股票名稱")
                    m_out: Dict[str, Any] = {
                        **m,
                        "date": _iso_date(date),
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                    }
                    docs.append(m_out)
                return docs
            return []
        time.sleep(sleep_s)
    return []

def fetch_bfi82u(date: dt.date, retry: int = 3, sleep_s: float = 0.6) -> Optional[Dict[str, Any]]:
    """
    Fetch BFI82U (三大法人買賣金額統計表) for the given date.
    """
    params = {
        "response": "json",
        "dayDate": _yyyymmdd(date),
        "type": "day",
    }
    s = _session()
    for _ in range(retry):
        r = _safe_get(s, BFI82U_URL, params)
        if not r:
            continue
        if r.ok:
            js = r.json()
            if js.get("stat") == "OK" and js.get("data"):
                fields: List[str] = js.get("fields", [])
                rows: List[List[Any]] = js.get("data", [])
                doc: Dict[str, Any] = {
                    "date": _iso_date(date),
                    "fields": fields,
                    "rows": [
                        {fields[idx]: row[idx] for idx in range(min(len(fields), len(row)))}
                        for row in rows
                    ],
                }
                return doc
            return None
        time.sleep(sleep_s)
    return None
