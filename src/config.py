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

# --- 配置缓存 ---
# 只缓存69-94行的关键配置项，其他配置不缓存
_CONFIG_CACHE_KEYS = {
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL_NAME", "PROXY_URL",
    "NTFY_TOPIC_URL", "GOTIFY_URL", "GOTIFY_TOKEN", "BARK_URL",
    "WX_BOT_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "WEBHOOK_URL", "WEBHOOK_METHOD", "WEBHOOK_HEADERS", "WEBHOOK_CONTENT_TYPE",
    "WEBHOOK_QUERY_PARAMETERS", "WEBHOOK_BODY",
    "PCURL_TO_MOBILE", "RUN_HEADLESS", "LOGIN_IS_EDGE", "RUNNING_IN_DOCKER",
    "AI_DEBUG_MODE", "SKIP_AI_ANALYSIS", "ENABLE_THINKING", "ENABLE_RESPONSE_FORMAT",
    "WEBHOOK_ENABLE_MARKDOWN"
}
_ai_config_cache = {}

def _mask_sensitive_value(key: str, value: str) -> str:
    """
    对敏感配置值进行脱敏处理，用于日志打印
    """
    sensitive_keys = {"OPENAI_API_KEY", "GOTIFY_TOKEN", "TELEGRAM_BOT_TOKEN", "WX_BOT_URL"}
    if key in sensitive_keys and value:
        if len(value) > 8:
            return f"{value[:4]}****{value[-4:]}"
        else:
            return "****"
    return value

def get_ai_config(key: str, default: str = None) -> str:
    """
    从缓存或环境变量获取配置，优先使用缓存
    只缓存白名单中的配置项（69-94行），避免缓存膨胀
    """
    # 只缓存白名单中的配置项
    if key not in _CONFIG_CACHE_KEYS:
        # 不在白名单中，直接返回环境变量值，不缓存
        return os.getenv(key, default)
    
    # 优先从缓存读取
    if key in _ai_config_cache:
        return _ai_config_cache[key]
    # 缓存不存在则从环境变量读取
    value = os.getenv(key, default)
    # 如果环境变量有值，同时更新缓存（只缓存白名单中的项）
    if value:
        _ai_config_cache[key] = value
        # 打印缓存初始化日志
        masked_value = _mask_sensitive_value(key, value)
        print(f"[配置缓存] 初始化缓存: {key} = {masked_value}")
    return value

def update_ai_config_cache(settings: dict):
    """
    更新配置缓存
    只更新白名单中的配置项（69-94行），避免缓存膨胀
    """
    global _ai_config_cache
    # 只更新白名单中的配置项
    filtered_settings = {k: v for k, v in settings.items() if k in _CONFIG_CACHE_KEYS}
    
    if filtered_settings:
        print(f"[配置缓存] 开始更新缓存，共 {len(filtered_settings)} 项配置")
        # 打印更新的配置项（敏感信息脱敏）
        for key, value in filtered_settings.items():
            masked_value = _mask_sensitive_value(key, str(value) if value else "")
            old_value = _ai_config_cache.get(key, "未设置")
            old_masked = _mask_sensitive_value(key, str(old_value) if old_value else "")
            if value != old_value:
                print(f"[配置缓存] 更新: {key} = {masked_value} (原值: {old_masked})")
            else:
                print(f"[配置缓存] 保持: {key} = {masked_value}")
    
    _ai_config_cache.update(filtered_settings)
    # 同时更新环境变量，确保兼容性（包括空值，以支持清空配置）
    for key, value in filtered_settings.items():
        if value:
            os.environ[key] = value
        else:
            # 如果值为空，从环境变量中删除（如果存在）
            os.environ.pop(key, None)
    
    if filtered_settings:
        print(f"[配置缓存] 缓存更新完成，当前缓存项数: {len(_ai_config_cache)}")

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
# 使用缓存机制读取配置（69-94行的所有配置项都会被缓存）
API_KEY = get_ai_config("OPENAI_API_KEY")
BASE_URL = get_ai_config("OPENAI_BASE_URL")
MODEL_NAME = get_ai_config("OPENAI_MODEL_NAME")
PROXY_URL = get_ai_config("PROXY_URL")
NTFY_TOPIC_URL = get_ai_config("NTFY_TOPIC_URL")
GOTIFY_URL = get_ai_config("GOTIFY_URL")
GOTIFY_TOKEN = get_ai_config("GOTIFY_TOKEN")
BARK_URL = get_ai_config("BARK_URL")
WX_BOT_URL = get_ai_config("WX_BOT_URL")
TELEGRAM_BOT_TOKEN = get_ai_config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_ai_config("TELEGRAM_CHAT_ID")
WEBHOOK_URL = get_ai_config("WEBHOOK_URL")
WEBHOOK_METHOD = get_ai_config("WEBHOOK_METHOD", "POST").upper()
WEBHOOK_HEADERS = get_ai_config("WEBHOOK_HEADERS")
WEBHOOK_CONTENT_TYPE = get_ai_config("WEBHOOK_CONTENT_TYPE", "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = get_ai_config("WEBHOOK_QUERY_PARAMETERS")
WEBHOOK_BODY = get_ai_config("WEBHOOK_BODY")
PCURL_TO_MOBILE = get_ai_config("PCURL_TO_MOBILE", "false").lower() == "true"
RUN_HEADLESS = get_ai_config("RUN_HEADLESS", "true").lower() != "false"
LOGIN_IS_EDGE = get_ai_config("LOGIN_IS_EDGE", "false").lower() == "true"
RUNNING_IN_DOCKER = get_ai_config("RUNNING_IN_DOCKER", "false").lower() == "true"
AI_DEBUG_MODE = get_ai_config("AI_DEBUG_MODE", "false").lower() == "true"
SKIP_AI_ANALYSIS = get_ai_config("SKIP_AI_ANALYSIS", "false").lower() == "true"
ENABLE_THINKING = get_ai_config("ENABLE_THINKING", "false").lower() == "true"
ENABLE_RESPONSE_FORMAT = get_ai_config("ENABLE_RESPONSE_FORMAT", "true").lower() == "true"
WEBHOOK_ENABLE_MARKDOWN = get_ai_config("WEBHOOK_ENABLE_MARKDOWN", "false").lower() == "true"

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
    
    print("[AI客户端] 开始初始化AI客户端...")
    
    # 从缓存或环境变量重新读取配置
    api_key = get_ai_config("OPENAI_API_KEY")
    base_url = get_ai_config("OPENAI_BASE_URL")
    model_name = get_ai_config("OPENAI_MODEL_NAME")
    proxy_url = get_ai_config("PROXY_URL")
    
    # 打印当前使用的配置（敏感信息脱敏）
    masked_api_key = _mask_sensitive_value("OPENAI_API_KEY", api_key if api_key else "")
    print(f"[AI客户端] 配置信息:")
    print(f"  - BASE_URL: {base_url}")
    print(f"  - MODEL_NAME: {model_name}")
    print(f"  - API_KEY: {masked_api_key}")
    print(f"  - PROXY_URL: {proxy_url if proxy_url else '未设置'}")
    
    # 检查配置是否齐全
    if not all([base_url, model_name]):
        print("[AI客户端] 警告：未在配置中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
        client = None
        return False
    
    try:
        if proxy_url:
            print(f"[AI客户端] 正在为AI请求使用HTTP/S代理: {proxy_url}")
            # httpx 会自动从环境变量中读取代理设置
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
        else:
            # 清除代理设置
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)

        # openai 客户端内部的 httpx 会自动从环境变量中获取代理配置
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        print(f"[AI客户端] AI客户端初始化成功: BASE_URL={base_url}, MODEL_NAME={model_name}")
        return True
    except Exception as e:
        print(f"[AI客户端] 初始化 OpenAI 客户端时出错: {e}")
        client = None
        return False

# 初始加载时打印缓存信息
def _print_cache_summary():
    """打印当前缓存摘要信息"""
    if _ai_config_cache:
        print(f"[配置缓存] 模块初始化完成，当前缓存了 {len(_ai_config_cache)} 项配置:")
        for key in sorted(_ai_config_cache.keys()):
            value = _ai_config_cache[key]
            masked_value = _mask_sensitive_value(key, value if value else "")
            print(f"  - {key}: {masked_value}")
    else:
        print("[配置缓存] 模块初始化完成，缓存为空（将从环境变量读取）")

# 初始加载时初始化client
if not all([BASE_URL, MODEL_NAME]):
    print("警告：未在 .env 文件中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
    client = None
else:
    init_ai_client()

# 打印缓存摘要（延迟打印，确保所有配置都已加载）
_print_cache_summary()

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
