# AIPet Backend 项目文档

## 项目概览

本项目为基于 Django + DRF + MySQL 的后端服务，提供用户、任务、动作、宠物模型、货币资产、玩法任务、成就、家具、道具等模块的接口，并使用 JWT 进行统一身份认证。所有接口同时支持 **JSON** 和 **Protobuf 二进制**两种格式（通过 `Content-Type` / `Accept` 头切换）。

## 技术栈

| 组件 | 版本 |
|---|---|
| Python | 3.11 |
| Django | 5.2.12 |
| Django REST Framework | 3.16.1 |
| MySQL | 8.x |
| djangorestframework-simplejwt | 5.5.1 |
| google-protobuf / grpc_tools | 最新 |
| mysqlclient | 2.2.8 |

## 项目结构

```
djangoProject/
├── aipet_backend/              # 项目主配置（settings、urls、wsgi）
├── aipet/                      # AI 宠物模型生成工作流（纯业务逻辑层）
│   ├── task_workflow.py        # 工作流统一入口（被 user_task/views.py 调用）
│   ├── CleanPic.py             # YOLO 宠物检测 + rembg 背景去除
│   ├── Meshy3D.py              # Meshy.ai API 封装（提交/查询）
│   ├── Meshy_Workflow.py       # Meshy 工作流状态机
│   ├── UVretexture.py          # UV 贴图后处理
│   ├── image_data_url.py       # 图片 → base64 data URL 工具
│   └── 3Dmodels/
│       ├── Sample/             # 参考 3D 模型（model0107.fbx）
│       └── meshy/              # Meshy 生成结果下载目录（按 task_id 分子目录）
├── app/
│   ├── user/                   # 用户模块
│   ├── user_task/              # 用户任务模块（含 AI 生成流程调用）
│   ├── pet_action/             # 动作模块
│   ├── pet_model/              # 宠物模型模块
│   ├── user_task_action_relation/  # 任务-动作关系模块
│   ├── wealth/                 # 货币资产模块
│   ├── user_wealth_relation/   # 用户-货币资产关系模块
│   ├── playtask/               # 玩法任务模块
│   ├── user_playtask_relation/ # 用户-玩法任务关系模块
│   ├── achievement/            # 成就模块
│   ├── user_achievement_relation/  # 用户-成就关系模块
│   ├── furniture/              # 家具模块
│   ├── user_furniture_relation/    # 用户-家具关系模块
│   ├── property/               # 道具模块
│   ├── user_property_relation/ # 用户-道具关系模块
│   ├── proto/                  # Protobuf .proto 文件及生成的 _pb2.py
│   ├── permissions.py          # 自定义 JWT 认证与权限
│   ├── utils.py                # 统一响应格式
│   ├── proto_registry.py       # Protobuf 分发注册表
│   └── log_middleware.py       # 请求日志中间件
├── templates/                  # 前端测试页面（HTML）
│   ├── index.html              # 接口测试中心导航页
│   ├── user.html               # 用户模块测试页
│   ├── user_task.html          # 用户任务 + AI 工作流测试页
│   ├── wealth.html             # 货币资产模块测试页
│   ├── playtask.html           # 玩法任务模块测试页
│   ├── achievement.html        # 成就模块测试页
│   ├── furniture.html          # 家具模块测试页
│   └── property.html           # 道具模块测试页
├── logs/                       # 日志文件目录
├── manage.py
└── requirements.txt
```

## 数据库表结构

| 表名 | 主键 | 核心字段 | 说明 |
|---|---|---|---|
| user | user_id | user_name, user_phone_number, user_password, user_profile_picture, user_mail_address, **user_status** | 用户基础信息表；密码哈希存储；user_status 为整型状态值（字典项配置） |
| user_task | user_task_id (UUID) | user_id(FK), task_name, created_at, workflow_status, image_path, pet_breed, pet_type, meshy_job_id, meshy_retry_count, texture_clean_path, workflow_error, pet_model_id | 用户任务表；同一用户下 task_name 不可重复；主键为 UUID 字符串（非自增整数） |
| pet_action | pet_action_id | pet_action_name | 动作字典表 |
| pet_model | pet_model_id | pet_model_name | 宠物模型字典表 |
| user_task_action_relation | relation_id | user_task_id(FK), pet_action_id(FK) | 任务-动作关系表（同一任务同一动作唯一） |
| wealth | wealth_id | wealth_name | 货币资产字典表（金币/钻石/积分等，名称全局唯一） |
| user_wealth_relation | id | user_id(FK), wealth_id(FK) | 用户-货币资产关系表 |
| playtask | playtask_id | playtask_name | 玩法任务字典表 |
| user_playtask_relation | id | user_id(FK), playtask_id(FK) | 用户-玩法任务关系表 |
| achievement | achievement_id | achievement_name | 成就字典表 |
| user_achievement_relation | id | user_id(FK), achievement_id(FK) | 用户-成就关系表 |
| furniture | furniture_id | furniture_name | 家具字典表 |
| user_furniture_relation | id | user_id(FK), furniture_id(FK) | 用户-家具关系表 |
| property | property_id | property_name | 道具字典表 |
| user_property_relation | id | user_id(FK), property_id(FK) | 用户-道具关系表 |

### user_task 字段详情

> 主键已由 `AutoField(int)` 改为 `CharField(UUID, max_length=36)`，与 AI 生成流程的文件命名保持一致。

| 字段 | 类型 | 说明 |
|---|---|---|
| user_task_id | VARCHAR(36) PK | UUID 字符串主键（由业务层在写库前预生成） |
| user_id | INT FK | 所属用户（→ user.user_id） |
| task_name | VARCHAR(200) | 任务名称，同一用户下唯一 |
| created_at | DATETIME | 创建时间（auto_now_add，用于列表按时间倒序） |
| workflow_status | VARCHAR(32) | AI 工作流当前状态（见下方枚举） |
| image_path | VARCHAR(512) | CleanPic 处理后图片的本地相对路径 |
| pet_breed | VARCHAR(100) | YOLO 识别到的宠物品种（如 British Shorthair） |
| pet_type | VARCHAR(20) | YOLO 识别到的宠物类型（cat / dog） |
| meshy_job_id | VARCHAR(200) | Meshy.ai 任务 ID |
| meshy_retry_count | INT DEFAULT 0 | Meshy 已重试次数（上限 2 次） |
| texture_clean_path | VARCHAR(512) | UV 贴图清理后的本地路径 |
| workflow_error | TEXT | 错误信息（空字符串 = 无错误） |
| pet_model_id | INT DEFAULT 0 | 关联的宠物模型ID（0 = 未生成，生成完成后由业务层写入） |

**唯一约束：** `(user_id, task_name)`

**workflow_status 枚举：**

| 值 | 含义 |
|---|---|
| `cleaned` | 图片预处理完成（任务创建时的初始状态） |
| `meshy_pending` | Meshy 任务已提交，等待队列 |
| `IN_PROGRESS` | Meshy 生成中 |
| `resubmit_pending` | Meshy 失败后重新提交中 |
| `meshy_done` | Meshy 生成完成，开始下载/处理贴图 |
| `TEXTURE_PROCESSING` | UV 贴图清理中 |
| `DONE` | 全部完成 ✅ |
| `FAILED` | Meshy 失败，已超重试上限 ❌ |
| `ERROR` | 本地处理错误（见 workflow_error）❌ |

---

## 用户状态字段说明（user_status）

`user_status` 为 `INT` 类型，默认值 `0`，后续通过字典项配置每个值的含义，当前约定：

| 值 | 含义 |
|---|---|
| 0 | 新玩家，服务器不存在贴图 |
| 1 | 已上传照片，贴图未制作完 |
| 2 | 已上传照片，服务器存在贴图 |

## 关联逻辑

```
User (1) ───────< UserTask (N)
UserTask (N) >───< PetAction (N)   via user_task_action_relation

User (N) >───< Wealth      (N)     via user_wealth_relation
User (N) >───< Playtask    (N)     via user_playtask_relation
User (N) >───< Achievement (N)     via user_achievement_relation
User (N) >───< Furniture   (N)     via user_furniture_relation
User (N) >───< Property    (N)     via user_property_relation

PetModel: 独立字典表（当前不与 User / UserTask 直接关联）
```

## 通用说明

### 认证方式

- 默认所有接口需要登录，请求头携带：`Authorization: Bearer <access_token>`
- 例外：注册（`createUser`）、登录（`dirUser` POST）允许匿名访问

> ⚠️ **临时兼容模式（前端未接入 token 期间有效）**
>
> `user` 和 `user_task` 两个模块的需登录接口，当前已临时放开权限（`AllowAny`），支持前端通过请求体或 query 参数传入 `user_phone_number` 代替 token 完成身份识别。
>
> - **POST/PUT 请求**：在请求体 JSON 中加 `"user_phone_number": "13800000000"`
> - **GET 请求**：在 URL 参数中加 `?user_phone_number=13800000000`
>
> 实现位置：`app/permissions.py` → `get_user_from_request(request)`，优先读 JWT token，取不到则查手机号。原有 token 校验代码均以注释形式保留，前端接入 token 后按注释提示还原即可。
>
> **涉及文件：**
> - `app/permissions.py`：新增 `get_user_from_request`
> - `app/user/views.py`：`update_user`、`dir_user GET` 改为 `AllowAny` + 手机号兜底
> - `app/user_task/views.py`：整个 ViewSet 改为 `AllowAny`，覆写 `get_queryset()`，所有 `request.user` 替换为 `request_user`

### 统一响应格式

成功：
```json
{
  "result": "success",
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

失败：
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": "错误说明 或 {\"field\": [\"校验错误\"]}"
}
```

### Protobuf 格式切换

| 场景 | Header |
|---|---|
| 请求体使用 Protobuf | `Content-Type: application/x-protobuf` |
| 期望 Protobuf 响应 | `Accept: application/x-protobuf` |
| 默认 JSON | 不设置或 `Accept: application/json` |

---

# API 文档

## 1. 用户模块（/api/users/）

### 1.1 用户注册

- **接口**：`POST /api/users/createUser/`
- **认证**：否（匿名允许）
- **说明**：手机号注册，系统自动生成 `user_name`，注册后 `user_status` 默认为 `0`（正常）

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_phone_number | string | 是 | 中国大陆 11 位手机号，全局唯一 |
| user_password | string | 是 | 密码，至少 6 位 |
| user_password_confirm | string | 是 | 密码确认，必须与 user_password 一致 |
| user_phone_code | string | 是 | 手机验证码（占位，暂不校验真实短信） |

**请求示例：**
```json
{
  "user_phone_number": "13800000000",
  "user_password": "123456",
  "user_password_confirm": "123456",
  "user_phone_code": "1234"
}
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "user_a1B2c3D4",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null,
    "user_status": 0
  },
  "message": "注册成功"
}
```

**失败响应（字段校验）：**
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": { "user_phone_number": ["手机号已存在"] }
}
```

---

### 1.2 用户登录

- **接口**：`POST /api/users/dirUser/`
- **认证**：否（匿名允许）
- **说明**：支持手机号+密码 或 手机号+验证码两种方式

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_phone_number | string | 是 | 登录手机号 |
| login_type | string | 是 | `password` 或 `code` |
| user_password | string | 条件 | login_type=password 时必填 |
| user_phone_code | string | 条件 | login_type=code 时必填 |

**请求示例（密码登录）：**
```json
{
  "user_phone_number": "13800000000",
  "login_type": "password",
  "user_password": "123456"
}
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user": {
      "user_id": 1,
      "user_name": "user_a1B2c3D4",
      "user_profile_picture": null,
      "user_phone_number": "13800000000",
      "user_mail_address": null,
      "user_status": 0,
      "pet_model_id": 0
    },
    "token": {
      "access_token": "<access_token>",
      "refresh_token": "<refresh_token>"
    }
  },
  "message": "登录成功"
}
```

**失败响应：**
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": "密码错误"
}
```

---

### 1.3 用户信息查询

- **接口**：`GET /api/users/dirUser/`
- **认证**：是
- **说明**：只能查询当前登录用户本人

**Query 参数（二选一）：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | int | 否 | 与 user_phone_number 二选一 |
| user_phone_number | string | 否 | 与 user_id 二选一 |

**请求示例：**
```
GET /api/users/dirUser/?user_id=1
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "user_a1B2c3D4",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null,
    "user_status": 0,
    "pet_model_id": 0
  },
  "message": "查询成功"
}
```

---

### 1.4 用户信息修改

- **接口**：`PUT /api/users/updateUser/`
- **认证**：是
- **说明**：当前允许修改 `user_name` 和 `user_status`，均为可选字段（partial update）

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_name | string | 否 | 新昵称 |
| user_status | int | 否 | 用户状态值，含义由字典项配置 |

**请求示例：**
```json
{
  "user_name": "Jerry",
  "user_status": 1
}
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "Jerry",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null,
    "user_status": 1
  },
  "message": "修改成功"
}
```

---

### 1.5 查询用户状态

- **接口**：`GET /api/users/dirUserStatus/`
- **认证**：否（临时兼容：通过 query 参数 `user_phone_number` 识别用户）
- **说明**：仅返回 `user_status`，供前端判断玩家当前状态

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_phone_number | string | 是（无 token 时） | 手机号，临时兼容用 |

**请求示例：**
```
GET /api/users/dirUserStatus/?user_phone_number=13800000000
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "user_status": 0 },
  "message": "查询成功"
}
```

**user_status 含义：**

| 值 | 含义 |
|---|---|
| 0 | 新玩家，服务器不存在贴图 |
| 1 | 已上传照片，贴图未制作完 |
| 2 | 已上传照片，服务器存在贴图 |

---

## 2. 动作模块（/api/actions/）

### 2.1 创建动作

- **接口**：`POST /api/actions/createAction/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_action_name | string | 是 | 动作名称 |

**请求示例：**
```json
{ "pet_action_name": "run" }
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "pet_action_id": 1, "pet_action_name": "run" },
  "message": "创建成功"
}
```

### 2.2 查询动作

- **接口**：`GET /api/actions/dirAction/?pet_action_id=1`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "pet_action_id": 1, "pet_action_name": "run" },
  "message": "查询成功"
}
```

---

## 3. 宠物模型模块（/api/pet-models/）

### 3.1 创建模型

- **接口**：`POST /api/pet-models/createModel/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_model_name | string | 是 | 模型名称 |

**请求示例：**
```json
{ "pet_model_name": "cat" }
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "pet_model_id": 1, "pet_model_name": "cat" },
  "message": "创建成功"
}
```

### 3.2 查询模型

- **接口**：`GET /api/pet-models/dirModel/?pet_model_id=1`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "pet_model_id": 1, "pet_model_name": "cat" },
  "message": "查询成功"
}
```

---

## 4. 用户任务模块（/api/models/）

> 所有接口均需登录，数据自动隔离（只能操作当前登录用户的任务）。  
> `user_task_id` 为 **UUID 字符串**，非整数。

### 4.1 创建任务并启动 AI 生成流程

- **接口**：`POST /api/models/createUserTask/`
- **认证**：是
- **Content-Type**：`multipart/form-data`（文件上传，非 JSON）

**表单字段：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| image | file | 是 | 宠物图片，≤5MB，仅支持图片格式 |
| CatSizeID | int | 否 | 模型尺寸：`10`=Cat_M、`20`=Cat_L、`30`=Cat_XL，默认 `10` |

**完整执行流程（同步）：**
1. 取注册时预创建的 `UserTask` 记录
2. 调用 `CleanPic`：YOLO 检测宠物 → rembg 去背景 → 保存清图
3. 预处理失败 → 直接返回错误，**不写库**（用户可重新上传）
4. 预处理成功 → 更新 `UserTask` 记录（`workflow_status=cleaned`），用户状态更新为 `1`
5. 根据 `CatSizeID` 选择对应 fbx 模型，调用 Meshy.ai 提交 retexture 任务
6. 同步写入 `pet_model_id`（10→1、20→2、30→3），保存状态并返回响应

**副作用：** 任务创建成功后，当前用户的 `user_status` 自动更新为 `1`（已上传图片、待收到贴图）；`pet_model_id` 根据 `CatSizeID` 同步写入。

**成功响应 201：**
```json
{
  "result": "success",
  "success": true,
  "message": "任务创建成功",
  "data": {
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "task_name": "mao",
    "workflow_status": "meshy_pending",
    "meshy_job_id": "meshy-job-id-string",
    "pet_breed": "British Shorthair",
    "pet_type": "cat"
  }
}
```

**错误响应：**

| result 值 | 触发场景 |
|---|---|
| `imgNone` | 未上传图片 |
| `imgOnly` | 非图片格式 |
| `tooLarge` | 图片超过 5MB |
| `taskNone` | 用户暂无预创建任务（需联系管理员） |
| `undetected` | YOLO 未检测到宠物 |
| `fail` | 图片处理失败 / Meshy 提交失败 |

---

### 4.2 轮询 Meshy 任务状态

- **接口**：`GET /api/models/queryMeshyTask/`
- **认证**：是
- **说明**：每次调用都向 Meshy.ai 查询最新状态并推进工作流；建议前端每 5 秒轮询一次，遇到终态（`DONE` / `FAILED` / `ERROR`）后停止

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |

**进行中响应：**
```json
{
  "result": "success",
  "data": {
    "task_id": "uuid",
    "workflow_status": "IN_PROGRESS",
    "workflow_error": ""
  }
}
```

**完成响应（workflow_status=DONE）：**
```json
{
  "result": "success",
  "data": {
    "task_id": "uuid",
    "workflow_status": "DONE",
    "texture_download_url": "https://cdn.meshy.ai/...",
    "texture_clean_path": "3Dmodels/meshy/<uuid>/texture_clean.png"
  }
}
```

**副作用：** 当 `workflow_status` 变为 `DONE` 时，当前用户的 `user_status` 自动更新为 `2`（已完成完整 AI 生成流程）。

---

### 4.3 修改任务名

- **接口**：`PUT /api/models/updateUserTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |
| task_name | string | 是 | 新任务名（同用户下不可重复） |

**请求示例：**
```json
{
  "user_task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "task_name": "新名称"
}
```

---

### 4.4 查询单个任务

- **接口**：`GET /api/models/dirUserTask/`
- **认证**：是

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |

**请求示例：**
```
GET /api/models/dirUserTask/?user_task_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

### 4.5 查询当前用户任务列表

- **接口**：`GET /api/models/dirUserTaskListByUser/`
- **认证**：是
- **说明**：按 `created_at` 倒序返回，无需额外参数

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "user_task_id": "uuid-B", "user_id": 1, "task_name": "任务B" },
    { "user_task_id": "uuid-A", "user_id": 1, "task_name": "任务A" }
  ],
  "message": "查询成功"
}
```

---

### 4.6 查询任务的 pet_model_id

- **接口**：`GET /api/models/dirPetModelId/`
- **认证**：是

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "message": "查询成功",
  "data": {
    "user_task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "pet_model_id": 0
  }
}
```

> `pet_model_id` 为 `0` 表示尚未关联模型。

---

### 4.7 更新任务的 pet_model_id

- **接口**：`PUT /api/models/updatePetModelId/`
- **认证**：是

**请求体（JSON）：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |
| pet_model_id | int | 是 | 要关联的宠物模型ID |

**请求示例：**
```json
{
  "user_task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "pet_model_id": 3
}
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "message": "更新成功",
  "data": {
    "user_task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "pet_model_id": 3
  }
}
```

---

## 5. 任务-动作关系模块（/api/task-actions/）

### 5.1 绑定动作到任务

- **接口**：`POST /api/task-actions/bindActionToTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

### 5.2 解绑动作与任务

- **接口**：`POST /api/task-actions/unbindActionFromTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | string (UUID) | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

### 5.3 查询任务的动作列表

- **接口**：`GET /api/task-actions/dirActionListByTask/?user_task_id=<uuid>`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "pet_action_id": 1, "pet_action_name": "run" },
    { "pet_action_id": 2, "pet_action_name": "sit" }
  ],
  "message": "查询成功"
}
```

---

## 6. 货币资产模块（/api/wealth/ 和 /api/user-wealth/）

字典表管理货币资产种类（金币、钻石、积分等），用户通过关系接口与之绑定/解绑。

### 6.1 创建货币资产

- **接口**：`POST /api/wealth/createWealth/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| wealth_name | string | 是 | 资产名称，全局唯一 |

**请求示例：**
```json
{ "wealth_name": "金币" }
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "wealth_id": 1, "wealth_name": "金币" },
  "message": "创建成功"
}
```

### 6.2 修改货币资产

- **接口**：`PUT /api/wealth/updateWealth/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| wealth_id | int | 是 | 资产ID |
| wealth_name | string | 是 | 新名称 |

### 6.3 查询货币资产

- **接口**：`GET /api/wealth/dirWealth/?wealth_id=1`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "wealth_id": 1, "wealth_name": "金币" },
  "message": "查询成功"
}
```

### 6.4 绑定货币资产到用户

- **接口**：`POST /api/user-wealth/bindWealthToUser/`
- **认证**：是
- **说明**：user_id 从 Token 自动读取

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| wealth_id | int | 是 | 资产ID |

**请求示例：**
```json
{ "wealth_id": 1 }
```

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "user_id": 1, "wealth_id": 1 },
  "message": "绑定成功"
}
```

### 6.5 解绑货币资产与用户

- **接口**：`POST /api/user-wealth/unbindWealthFromUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| wealth_id | int | 是 | 资产ID |

### 6.6 查询用户的货币资产列表

- **接口**：`GET /api/user-wealth/dirWealthListByUser/`
- **认证**：是
- **说明**：无需额外参数，由 Token 自动识别当前用户

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "wealth_id": 1, "wealth_name": "金币" },
    { "wealth_id": 2, "wealth_name": "钻石" }
  ],
  "message": "查询成功"
}
```

---

## 7. 玩法任务模块（/api/playtask/ 和 /api/user-playtask/）

### 7.1 创建玩法任务

- **接口**：`POST /api/playtask/createPlaytask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| playtask_name | string | 是 | 任务名称 |

### 7.2 修改玩法任务

- **接口**：`PUT /api/playtask/updatePlaytask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| playtask_id | int | 是 | 任务ID |
| playtask_name | string | 是 | 新名称 |

### 7.3 查询玩法任务

- **接口**：`GET /api/playtask/dirPlaytask/?playtask_id=1`
- **认证**：是

### 7.4 绑定玩法任务到用户

- **接口**：`POST /api/user-playtask/bindPlaytaskToUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| playtask_id | int | 是 | 任务ID |

### 7.5 解绑玩法任务与用户

- **接口**：`POST /api/user-playtask/unbindPlaytaskFromUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| playtask_id | int | 是 | 任务ID |

### 7.6 查询用户的玩法任务列表

- **接口**：`GET /api/user-playtask/dirPlaytaskListByUser/`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "playtask_id": 1, "playtask_name": "每日签到" },
    { "playtask_id": 2, "playtask_name": "每周挑战" }
  ],
  "message": "查询成功"
}
```

---

## 8. 成就模块（/api/achievement/ 和 /api/user-achievement/）

### 8.1 创建成就

- **接口**：`POST /api/achievement/createAchievement/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| achievement_name | string | 是 | 成就名称 |

### 8.2 修改成就

- **接口**：`PUT /api/achievement/updateAchievement/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| achievement_id | int | 是 | 成就ID |
| achievement_name | string | 是 | 新名称 |

### 8.3 查询成就

- **接口**：`GET /api/achievement/dirAchievement/?achievement_id=1`
- **认证**：是

### 8.4 绑定成就到用户

- **接口**：`POST /api/user-achievement/bindAchievementToUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| achievement_id | int | 是 | 成就ID |

### 8.5 解绑成就与用户

- **接口**：`POST /api/user-achievement/unbindAchievementFromUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| achievement_id | int | 是 | 成就ID |

### 8.6 查询用户的成就列表

- **接口**：`GET /api/user-achievement/dirAchievementListByUser/`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "achievement_id": 1, "achievement_name": "初学者" },
    { "achievement_id": 2, "achievement_name": "连续签到7天" }
  ],
  "message": "查询成功"
}
```

---

## 9. 家具模块（/api/furniture/ 和 /api/user-furniture/）

### 9.1 创建家具

- **接口**：`POST /api/furniture/createFurniture/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| furniture_name | string | 是 | 家具名称 |

### 9.2 修改家具

- **接口**：`PUT /api/furniture/updateFurniture/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| furniture_id | int | 是 | 家具ID |
| furniture_name | string | 是 | 新名称 |

### 9.3 查询家具

- **接口**：`GET /api/furniture/dirFurniture/?furniture_id=1`
- **认证**：是

### 9.4 绑定家具到用户

- **接口**：`POST /api/user-furniture/bindFurnitureToUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| furniture_id | int | 是 | 家具ID |

### 9.5 解绑家具与用户

- **接口**：`POST /api/user-furniture/unbindFurnitureFromUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| furniture_id | int | 是 | 家具ID |

### 9.6 查询用户的家具列表

- **接口**：`GET /api/user-furniture/dirFurnitureListByUser/`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "furniture_id": 1, "furniture_name": "沙发" },
    { "furniture_id": 2, "furniture_name": "书桌" }
  ],
  "message": "查询成功"
}
```

---

## 10. 道具模块（/api/property/ 和 /api/user-property/）

### 10.1 创建道具

- **接口**：`POST /api/property/createProperty/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| property_name | string | 是 | 道具名称 |

### 10.2 修改道具

- **接口**：`PUT /api/property/updateProperty/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| property_id | int | 是 | 道具ID |
| property_name | string | 是 | 新名称 |

### 10.3 查询道具

- **接口**：`GET /api/property/dirProperty/?property_id=1`
- **认证**：是

### 10.4 绑定道具到用户

- **接口**：`POST /api/user-property/bindPropertyToUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| property_id | int | 是 | 道具ID |

### 10.5 解绑道具与用户

- **接口**：`POST /api/user-property/unbindPropertyFromUser/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| property_id | int | 是 | 道具ID |

### 10.6 查询用户的道具列表

- **接口**：`GET /api/user-property/dirPropertyListByUser/`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "property_id": 1, "property_name": "血瓶" },
    { "property_id": 2, "property_name": "经验药水" }
  ],
  "message": "查询成功"
}
```

---

## 11. JWT 刷新与校验

### 11.1 刷新 Token

- **接口**：`POST /api/auth/token/refresh/`
- **认证**：否

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| refresh | string | 是 | refresh_token |

**成功响应：**
```json
{ "access": "<new_access_token>" }
```

### 11.2 校验 Token

- **接口**：`POST /api/auth/token/verify/`
- **认证**：否

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| token | string | 是 | access_token 或 refresh_token |

**成功响应：**
```json
{}
```

---

## 测试页面入口

启动服务后访问 `http://127.0.0.1:8000/test/index/` 进入接口测试中心。

| 页面 | URL |
|---|---|
| 测试中心导航 | `/test/index/` |
| 用户模块 | `/test/user/` |
| 用户任务 + AI 工作流 | `/test/user_task/` |
| 货币资产模块 | `/test/wealth/` |
| 玩法任务模块 | `/test/playtask/` |
| 成就模块 | `/test/achievement/` |
| 家具模块 | `/test/furniture/` |
| 道具模块 | `/test/property/` |

---

## 变更记录

### 2026-04-30

**`app/utils.py`**
- `error_response` 新增 `result` 参数（默认 `"fail"`），支持自定义返回标识，向后兼容所有现有调用

**`app/user/serializers.py`**
- 密码校验规则：从"≥6位"改为"6~15位、仅限大小写字母和数字（无特殊字符）"

**`app/user/views.py`**
- 注册接口：提前判断手机号已存在，返回 `result="registered"`
- 登录接口：用户不存在返回 `result="unexist"`，密码错误返回 `result="fail"`
- `update_user`、`dir_user GET`：临时改为 `AllowAny`，通过 `get_user_from_request` 解析用户（原代码注释保留）

**`app/permissions.py`**
- 新增 `get_user_from_request(request)`：优先 JWT token，其次手机号查表（临时兼容）

**`app/user_task/views.py`**
- `queryMeshyTask`、`dirPetModelId`、`updatePetModelId`：移除 `user_task_id` 入参，改为通过 token/手机号关联查当前用户名下唯一任务
- `queryMeshyTask`：返回值中新增 `user_status` 字段
- 整个 ViewSet 权限临时改为 `AllowAny`，覆写 `get_queryset()` 通过 `get_user_from_request` 过滤（原代码注释保留）
- `createUserTask`：所有 `request.user` 替换为 `request_user`（原代码注释保留）
- 各错误场景补充自定义 `result` 标识：`imgnone`、`imgonly`、`toolarge`、`tasknameexist`、`undetected`、`tasknone`

---

### 2026-04-30（续）

**`app/user/views.py`**
- `createUser` 注册成功后同步创建一条空的 `UserTask`（`task_id=uuid4()`，`task_name="mao"`），用户名下任务在注册时即预创建
- 新增接口 `dirUserStatus`（`GET /api/users/dirUserStatus/`）：仅返回 `user_status`，临时兼容通过 `user_phone_number` query 参数识别用户

**`app/user_task/views.py`**
- `createUserTask` 重构：不再新建 UserTask，改为取注册时预创建的 task，将图片处理结果写入已有记录（`task_obj.save(update_fields=[...])`）；`task_name`、`task_id` 不再由前端传入或重新生成（原代码注释保留）
- 新增接口 `dirTaskResult`（`GET /api/models/dirTaskResult/`）：查询 `workflow_status=DONE` 的任务，将本地 `texture_clean_path` 转换为可访问的 `texture_download_url` 返回

**`aipet_backend/settings.py`**
- 新增 `MESHY_SERVER_URL`：服务器外网地址，用于拼接贴图下载 URL（本地开发用 `http://127.0.0.1:8000`，生产用 `http://42.193.98.94`）
- 新增 `SITE_URL`：同上，本地/生产注释切换

**nginx 配置说明**
- `location /meshy_images/` → `alias /www/wwwroot/djangoProject/aipet/3Dmodels/meshy/`
- `texture_clean_path`（DB 本地路径）→ `texture_download_url` 转换规则：截取 `meshy/` 之后的部分，拼接 `MESHY_SERVER_URL/meshy_images/`

---

### 新增接口汇总（2026-04-30）

| 接口 | 路径 | 说明 |
|---|---|---|
| 查询玩家状态 | `GET /api/users/dirUserStatus/?user_phone_number=xxx` | 仅返回 `user_status` |
| 查询贴图结果 | `GET /api/models/dirTaskResult/?user_phone_number=xxx` | 返回 DONE 任务的 `texture_download_url` |

---

### 2026-05-01

**`app/user/views.py`**
- `dirUser GET`（查询用户信息）：返回数据新增 `pet_model_id` 字段，取该用户名下 `UserTask` 的 `pet_model_id`，无 task 则返回 `0`
- `dirUser POST`（登录）：`user` 对象同步新增 `pet_model_id` 字段，逻辑同上

**`app/user_task/views.py`**
- `createUserTask`：新增表单字段 `CatSizeID`（可选，默认 `10`），映射关系 `10→Cat_M`、`20→Cat_L`、`30→Cat_XL`；提交 Meshy 后同步将 `pet_model_id`（`10→1`、`20→2`、`30→3`）写入 `UserTask`

---

## 开发命令速查

```bash
# 安装依赖
venv\Scripts\python.exe -m pip install -r requirements.txt

# 生成迁移
venv\Scripts\python.exe manage.py makemigrations

# 应用迁移
venv\Scripts\python.exe manage.py migrate

# 启动服务
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000

# 重新编译某个 proto 文件（以 user.proto 为例）
venv\Scripts\python.exe -m grpc_tools.protoc -I. -Ivenv/Lib/site-packages/grpc_tools/_proto --python_out=. app/proto/user.proto
```
