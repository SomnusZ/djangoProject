import requests, os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import time
import types

_AIPET_DIR = Path(__file__).resolve().parent

#meshy key
MESHY_API_KEY = "msy_gEKWTupXdr3URnK42d9p2E496hY1NjsoBTgn"
MESHY_API_BASE = "https://api.meshy.ai/openapi/v1"

class MeshyAPIError(Exception):
    """Meshy 返回异常或格式不符合预期"""

class MeshyRequestError(Exception):
    """请求 Meshy 失败（网络/超时/HTTP错误）"""

##Meshy生成
# { meshy_task_id: "..."},此阶段只会得到id，通过id去找对应的模型生成情况
def start_meshy_job(image_url: str,model_url:str) -> dict:
    payload = {
        "model_url":model_url, #模板解base64重复使用
        "image_style_url": image_url,
        "ai_model":"latest",
        "enable_pbr":False,
        "enable_original_uv":True
    }
    # headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    # resp = requests.post(f"{MESHY_API_BASE}/retexture", headers=headers, json=payload)
    # resp.raise_for_status()
    # data = resp.json()
    #
    # if "result" not in data:
    #     print("❌ Meshy 返回异常:", data)
    #     raise ValueError(f"Meshy response missing result: {data}")
    #
    # return {"job_id": data["result"]}
    # 弱网保护，请求三次
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    data = ''
    for i in range(3):
        try:
            resp = requests.post(f"{MESHY_API_BASE}/retexture", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "result" in data:
                return {"job_id": data["result"]}
        except Exception as e:
            data = str(e)
        time.sleep(2)

    print("❌ Meshy 返回异常:", data)
    raise ValueError(f"Meshy response missing result: {data}")


#根据id轮询找model_url
def check_meshy_status(meshy_task_id: str) -> dict:
    """查询任务状态"""
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    resp = requests.get(f"{MESHY_API_BASE}/retexture/{meshy_task_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()  #

def download_meshy_result(status: dict, meshy_task_id: str) -> dict:
    """
    下载 Meshy 的 fbx 模型 + 贴图
    """
    # 每个 task_id 独立文件夹用来区分不同用户的资产
    output_dir = _AIPET_DIR / "3Dmodels" / "meshy" / meshy_task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = {}

    def _download(url: str, filename: str):
        resp = requests.get(url)
        resp.raise_for_status()
        out_path = output_dir / filename
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return str(out_path)

    # 1. fbx模型
    # #供测试使用，后续只存贴图
    fbx_url = status.get("model_urls", {}).get("fbx")
    if fbx_url:
        saved_paths["fbx"] = _download(fbx_url, "model.fbx")

    # 2. 贴图
    textures = status.get("texture_urls", [])
    saved_paths["textures"] = []
    for idx, tex_dict in enumerate(textures):
        tex_paths = {}
        for tex_type, url in tex_dict.items():
            ext = Path(urlparse(url).path).suffix or ".png"
            tex_paths[tex_type] = _download(url, f"texture_{idx}_{tex_type}{ext}")
        saved_paths["textures"].append(tex_paths)

    return saved_paths






