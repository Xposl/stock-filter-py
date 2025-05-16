"""
测试定时任务端点
"""
import requests
import logging
import argparse
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cron_endpoint(host="localhost", port=8000, market="hk", token=None):
    """
    测试定时任务端点
    
    Args:
        host: 主机名
        port: 端口
        market: 市场代码 (hk, zh, us)
        token: 可选的认证令牌
    """
    url = f"http://{host}:{port}/investnote/cron/ticker/{market}/update"
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    logger.info(f"测试端点: {url}")
    logger.info(f"头信息: {headers}")
    
    try:
        response = requests.post(url, headers=headers)
        
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ 测试成功!")
        else:
            logger.error(f"❌ 测试失败: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='测试定时任务端点')
    parser.add_argument('--host', default='localhost', help='主机名')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--market', default='hk', choices=['hk', 'zh', 'us'], help='市场代码')
    parser.add_argument('--token', help='认证令牌')
    
    args = parser.parse_args()
    test_cron_endpoint(host=args.host, port=args.port, market=args.market, token=args.token)
