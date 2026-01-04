import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

# --- AI & Notification Configuration ---
load_dotenv()

# --- File Paths & Directories ---
STATE_FILE = "xianyu_state.json"
IMAGE_SAVE_DIR = "images"
CONFIG_FILE = "config.json"
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

# 任务隔离的临时图片目录前缀
TASK_IMAGE_DIR_PREFIX = "task_images_"

# --- API URL Patterns ---
API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search"
DETAIL_API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail"

# --- AI配置缓存 ---
_ai_config_cache = {}

def get_ai_config(key: str, default: str = None) -> str:
    """
    从缓存或环境变量获取AI配置，优先使用缓存
    """
    # 优先从缓存读取
    if key in _ai_config_cache:
        return _ai_config_cache[key]
    # 缓存不存在则从环境变量读取
    value = os.getenv(key, default)
    # 如果环境变量有值，同时更新缓存
    if value:
        _ai_config_cache[key] = value
    return value

def update_ai_config_cache(settings: dict):
    """
    更新AI配置缓存
    """
    global _ai_config_cache
    _ai_config_cache.update(settings)
    # 同时更新环境变量，确保兼容性（包括空值，以支持清空配置）
    for key, value in settings.items():
        if value:
            os.environ[key] = value
        else:
            # 如果值为空，从环境变量中删除（如果存在）
            os.environ.pop(key, None)

def clear_ai_config_cache():
    """
    清空AI配置缓存（用于重新从环境变量加载）
    """
    global _ai_config_cache
    _ai_config_cache.clear()

def get_ai_config_cache():
    """
    获取当前AI配置缓存
    """
    return _ai_config_cache.copy()

# --- Environment Variables ---
# 使用缓存机制读取配置
API_KEY = get_ai_config("OPENAI_API_KEY")
BASE_URL = get_ai_config("OPENAI_BASE_URL")
MODEL_NAME = get_ai_config("OPENAI_MODEL_NAME")
PROXY_URL = get_ai_config("PROXY_URL")
NTFY_TOPIC_URL = os.getenv("NTFY_TOPIC_URL")
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")
BARK_URL = os.getenv("BARK_URL")
WX_BOT_URL = os.getenv("WX_BOT_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_METHOD = os.getenv("WEBHOOK_METHOD", "POST").upper()
WEBHOOK_HEADERS = os.getenv("WEBHOOK_HEADERS")
WEBHOOK_CONTENT_TYPE = os.getenv("WEBHOOK_CONTENT_TYPE", "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = os.getenv("WEBHOOK_QUERY_PARAMETERS")
WEBHOOK_BODY = os.getenv("WEBHOOK_BODY")
PCURL_TO_MOBILE = os.getenv("PCURL_TO_MOBILE", "false").lower() == "true"
RUN_HEADLESS = os.getenv("RUN_HEADLESS", "true").lower() != "false"
LOGIN_IS_EDGE = os.getenv("LOGIN_IS_EDGE", "false").lower() == "true"
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
AI_DEBUG_MODE = os.getenv("AI_DEBUG_MODE", "false").lower() == "true"
SKIP_AI_ANALYSIS = os.getenv("SKIP_AI_ANALYSIS", "false").lower() == "true"
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "false").lower() == "true"
ENABLE_RESPONSE_FORMAT = os.getenv("ENABLE_RESPONSE_FORMAT", "true").lower() == "true"
WEBHOOK_ENABLE_MARKDOWN = os.getenv("WEBHOOK_ENABLE_MARKDOWN", "false").lower() == "true"

# --- Headers ---
IMAGE_DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# --- Client Initialization ---
client = None

def init_ai_client():
    """
    初始化或重新初始化AI客户端
    """
    global client
    
    # 从缓存或环境变量重新读取配置
    api_key = get_ai_config("OPENAI_API_KEY")
    base_url = get_ai_config("OPENAI_BASE_URL")
    model_name = get_ai_config("OPENAI_MODEL_NAME")
    proxy_url = get_ai_config("PROXY_URL")
    
    # 检查配置是否齐全
    if not all([base_url, model_name]):
        print("警告：未在配置中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
        client = None
        return False
    
    try:
        if proxy_url:
            print(f"正在为AI请求使用HTTP/S代理: {proxy_url}")
            # httpx 会自动从环境变量中读取代理设置
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
        else:
            # 清除代理设置
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)

        # openai 客户端内部的 httpx 会自动从环境变量中获取代理配置
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        print(f"AI客户端已初始化/更新: BASE_URL={base_url}, MODEL_NAME={model_name}")
        return True
    except Exception as e:
        print(f"初始化 OpenAI 客户端时出错: {e}")
        client = None
        return False

# 初始加载时初始化client
if not all([BASE_URL, MODEL_NAME]):
    print("警告：未在 .env 文件中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
    client = None
else:
    init_ai_client()

# 检查AI客户端是否成功初始化
if not client:
    # 在 prompt_generator.py 中，如果 client 为 None，会直接报错退出
    # 在 spider_v2.py 中，AI分析会跳过
    # 为了保持一致性，这里只打印警告，具体逻辑由调用方处理
    pass

# 检查关键配置
if not all([BASE_URL, MODEL_NAME]) and 'prompt_generator.py' in sys.argv[0]:
    sys.exit("错误：请确保在 .env 文件中完整设置了 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。(OPENAI_API_KEY 对于某些服务是可选的)")

def get_ai_request_params(**kwargs):
    """
    构建AI请求参数，根据ENABLE_THINKING和ENABLE_RESPONSE_FORMAT环境变量决定是否添加相应参数
    """
    if ENABLE_THINKING:
        kwargs["extra_body"] = {"enable_thinking": False}
    
    # 如果禁用response_format，则移除该参数
    if not ENABLE_RESPONSE_FORMAT and "response_format" in kwargs:
        del kwargs["response_format"]
    
    return kwargs
