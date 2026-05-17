from aipet.Meshy3D import download_meshy_result, start_meshy_job
from aipet.UVretexture import clean_uv_inpaint_by_task_id
from dataclasses import dataclass
from django.conf import settings

#服务器BASE
PUBLIC_BASE_URL="http://43.138.73.163"
#合并image url和model url
@dataclass
class MeshyContext:
    image_url: str
    model_url: str

# ===== 状态定义（全局常量）=====
# FAILED代表meshy失败，ERROR代表本地错误。并且用error_source进行区分
TERMINAL_STATUSES = {"DONE", "FAILED", "ERROR"}

def reset_meshy_pipeline_flags(task: dict):
    # 清 downloaded / cleaned状态，为重新贴图做好准备
    task["status"] = "resubmit_pending"
    task["meshy_downloaded"] = False
    task.pop("meshy_local_files", None)
    # 贴图清理
    task["texture_cleaned"] = False
    task.pop("texture_clean_path", None)
    # 清除旧错误
    task.pop("error", None)

def resubmit_meshy_job(task_id: str,task: dict,ctx: MeshyContext) -> str:
    """
    只在 Meshy FAILED 5...的场景下调用，不做本地校验
    """
    if task.get("status") != "FAILED":
        raise RuntimeError(
            f"resubmit_meshy_job called in invalid status: {task.get('status')}"
        )
    old_job_id = task.get("meshy_job_id")
    if not old_job_id:
        raise RuntimeError("Cannot resubmit: missing meshy_job_id")
    #记录旧job_id
    task.setdefault("meshy_job_history", []).append(old_job_id)
    #重新提交meshy
    try:
        result = start_meshy_job(
            image_url=ctx.image_url,
            model_url=ctx.model_url,
        )
    except Exception as e:
        # Meshy API 调用本身失败，属于系统级错误
        raise RuntimeError(f"Meshy resubmit failed: {repr(e)}")

    new_job_id = result["job_id"]
    task["meshy_job_id"] = new_job_id

    # 重置workflow标记
    reset_meshy_pipeline_flags(task)

    # 进入重试等待状态
    task["status"] = "resubmit_pending"
    task["meshy_retry_count"] = task.get("meshy_retry_count", 0) + 1
    task["last_retry_reason"] = "meshy_failed"
    return new_job_id

def advance_meshy_task(task_id: str, task: dict, meshy_status: dict,ctx: MeshyContext):
    status_value = meshy_status.get("status")
    # 1️⃣ 终态直接返回（幂等）
    if task.get("status") in TERMINAL_STATUSES:
        return

    # Meshy 仍在运行
    if status_value in ["PENDING", "IN_PROGRESS"]:
        task["status"] = status_value
        print(f"[Meshy][{task_id}] status = {status_value}")
        return

    # Meshy 失败
    if status_value == "FAILED":
        ##failed不重试逻辑
        # task["status"] = "FAILED"
        # print(f"[Meshy][{task_id}] ❌ Meshy FAILED")
        # return

        #由于meshy失败/崩溃，内部重试逻辑，用户不可见
        # 1.标记错误来源：这一步能保证“只因 Meshy 失败才允许进行重试”
        task["error_source"] = "MESHY"
        task["error"] = task.get("error") or "Meshy job failed"
        # 2.重试参数
        task.setdefault("meshy_retry_count", 0)
        task.setdefault("meshy_max_retries", 2)  # 最多重试 2 次

        # 3.准入判断：必须是 Meshy 失败导致 + 未超过重试次数
        can_retry=(
            task.get("error_source")=="MESHY"
            and task["meshy_retry_count"]<task["meshy_max_retries"]
        )

        if can_retry:
            try:
                print(f"[Meshy][{task_id}] 🔁 Resubmitting... "
                      f"({task['meshy_retry_count'] + 1}/{task['meshy_max_retries']})")

                # resubmit 内部会更新 task["meshy_job_id"] + reset flags + status="resubmit_pending"
                new_job_id = resubmit_meshy_job(task_id, task, ctx)
                print(f"[Meshy][{task_id}] ✅ Resubmitted new job_id={new_job_id}, status={task.get('status')}")
                return  # ✅ 立刻返回，下一次轮询会用新的 job_id 去查

            except Exception as e:
                # resubmit 自己都失败了，这就不是 Meshy job FAILED，而是系统层面问题
                task["status"] = "ERROR"
                task["error_source"] = "SYSTEM"
                task["error"] = f"[resubmit_meshy_job] {repr(e)}"
                print(f"[Meshy][{task_id}] ❌ Resubmit FAILED: {task['error']}")
                return
        # 4.达到最大fail次数，进入最终failed
        task["status"] = "FAILED"
        task["error"] = task.get("error") or "Meshy failed and retries exhausted"
        print(f"[Meshy][{task_id}] 🛑 Retries exhausted -> FAILED")
        return
    # Meshy 成功（核心）
    if status_value != "SUCCEEDED":
        return
    # 已经完整将贴图处理过
    if task.get("status") == "DONE":
        return

    print(f"[Meshy][{task_id}] ✅ Meshy SUCCEEDED")
    task["status"] = "meshy_done"

    # ===============================
    # 1️⃣ 下载
    # ===============================
    if not task.get("meshy_downloaded"):
        print(f"[Meshy][{task_id}] ⬇️  Downloading assets...")
        try:
            task["meshy_local_files"] = download_meshy_result(
                meshy_status, task_id
            )
            task["meshy_downloaded"] = True
            print(f"[Meshy][{task_id}] ✅ Download SUCCESS")
        except Exception as e:
            task["status"] = "ERROR"
            task["error_source"] = "LOCAL"
            task["error"] = f"[download] {e}"
            print(f"[Meshy][{task_id}] ❌ Download FAILED: {e}")
            return

    # ===============================
    # 2️⃣ 贴图清理
    # ===============================
    if not task.get("texture_cleaned"):
        print(f"[Texture][{task_id}] 🎨 Texture processing...")
        try:
            task["status"] = "TEXTURE_PROCESSING"
            task["texture_clean_path"] = clean_uv_inpaint_by_task_id(task_id)
            task["texture_cleaned"] = True
            print(f"[Texture][{task_id}] ✅ Texture CLEAN SUCCESS")
        except Exception as e:
            task["status"] = "ERROR"
            task["error_source"] = "LOCAL"
            task["error"] = f"[texture] {e}"
            print(f"[Texture][{task_id}] ❌ Texture CLEAN FAILED: {e}")
            return
    # ===============================
    # 全部完成
    # ===============================
    task["status"] = "DONE"
    print(f"[Task][{task_id}] 🎉 ALL DONE")

def get_texture_result(task_id: str, task: dict):
    status = task.get("status")

    if status == "DONE":
        # request 参数已移除，直接返回相对路径，由调用方决定是否拼绝对 URL
        # download_url = f"/meshy_images/{task_id}/texture_clean.png"
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        download_url = f"{site_url}/meshy_images/{task_id}/texture_clean.png"
        return {
            "texture_download_url": download_url
        }

    if status in ["FAILED", "ERROR"]:
        return {
            "task_id": task_id,
            "status": status,
            "error": task.get("error"),
        }

    return {
        "task_id": task_id,
        "status": status,
        "detail": "processing",
    }


#旧版main, async def meshy_status(task_id: str):
# task = TASKS.get(task_id)
    # if not task or "meshy_job_id" not in task:
    #     return {"error": "meshy job not found"}
    #
    # job_id = task["meshy_job_id"]
    #
    # # 已完成或失败的任务，不再重复推进
    # if task.get("status") in ["DONE", "FAILED", "ERROR"]:
    #     return {
    #         "task_id": task_id,
    #         "status": task["status"]
    #     }
    #
    # try:
    #     status = check_meshy_status(job_id)
    # except Exception as e:
    #     TASKS[task_id]["status"] = "ERROR"
    #     TASKS[task_id]["error"] = str(e)
    #     return {"task_id": task_id, "status": "ERROR"}
    #
    # status_value = status.get("status")
    #
    # # Meshy 仍在运行
    # if status_value in ["PENDING", "IN_PROGRESS"]:
    #     TASKS[task_id]["status"] = status_value
    #     return {"task_id": task_id, "status": status_value}
    #
    # # Meshy 失败
    # if status_value == "FAILED":
    #     TASKS[task_id]["status"] = "FAILED"
    #     return {"task_id": task_id, "status": "FAILED"}
    #
    # # Meshy 成功
    # if status_value == "SUCCEEDED":
    #     TASKS[task_id]["status"] = "meshy_done"
    #
    #     # 1️⃣ 下载 Meshy 结果（只做一次）
    #     if not TASKS[task_id].get("meshy_downloaded"):
    #         saved_paths = download_meshy_result(status, task_id)
    #         TASKS[task_id]["meshy_local_files"] = saved_paths
    #         TASKS[task_id]["meshy_downloaded"] = True
    #
    #     # 2️⃣ 贴图清理（只做一次）
    #     if not TASKS[task_id].get("texture_cleaned"):
    #         try:
    #             TASKS[task_id]["status"] = "TEXTURE_PROCESSING"
    #             clean_path = clean_uv_inpaint_by_task_id(task_id)
    #             TASKS[task_id]["texture_cleaned"] = True
    #             TASKS[task_id]["texture_clean_path"] = clean_path
    #             TASKS[task_id]["status"] = "DONE"
    #         except Exception as e:
    #             TASKS[task_id]["status"] = "ERROR"
    #             TASKS[task_id]["error"] = str(e)
    #
    #     return {
    #         "task_id": task_id,
    #         "status": TASKS[task_id]["status"]
    #     }
    #
    # return {"task_id": task_id, "status": status_value}