# AIPet Backend 项目文档

## 业务说明与表结构

**业务概览**
- 用户注册后拥有自己的任务（UserTask），任务属于用户（1 对多）。
- 动作（PetAction）是动作字典，本身不归属于某个用户。
- 任务与动作是多对多关系，通过中间表 `user_task_action_relation` 进行绑定/解绑。
- 宠物模型（PetModel）为模型字典，本身与用户/任务无强关联（当前版本为独立表）。

**表结构概览**
| 表名 | 主键 | 核心字段 | 说明 |
|---|---|---|---|
| user | user_id | user_name, user_profile_picture, user_phone_number, user_password, user_mail_address | 用户基础信息表（手机号唯一，密码为哈希） |
| user_task | user_task_id | user_id(FK), task_name | 用户任务表；同一用户下 task_name 不可重复 |
| pet_action | pet_action_id | pet_action_name | 动作字典表 |
| pet_model | pet_model_id | pet_model_name | 模型字典表 |
| user_task_action_relation | relation_id | user_task_id(FK), pet_action_id(FK) | 任务-动作关系表（同一任务同一动作唯一） |

**关联逻辑**
- User 1 —— N UserTask
- UserTask N —— N PetAction（通过 user_task_action_relation）
- PetModel：独立表（当前不与 UserTask / User 直接关联）

**关系示意（文本版）**
```
User (1) ───────< UserTask (N)
UserTask (N) >───< PetAction (N)
             \    (via user_task_action_relation)
PetModel 为独立字典表
```

AIPet Backend 项目文档

**Project Overview**
本项目为基于 Django + DRF + MySQL 的后端服务，提供用户、任务、动作、宠物模型及任务-动作关系等接口，并使用 JWT 进行统一身份认证。

**Tech Stack**
- Python 3.11
- Django 5.2.12
- Django REST framework 3.16.1
- MySQL 8.x
- djangorestframework-simplejwt 5.5.1
- mysqlclient 2.2.8

**Project Structure**
```
F:\workspace_Pycharm_git\djangoProject
├─ aipet_backend                  # 项目主配置
├─ app                            # 业务应用
│  ├─ user                        # 用户模块
│  ├─ user_task                   # 用户任务模块
│  ├─ pet_action                  # 动作模块
│  ├─ pet_model                   # 宠物模型模块
│  ├─ user_task_action_relation   # 任务-动作关系模块
│  ├─ permissions.py              # 自定义 JWT 认证与权限
│  ├─ utils.py                    # 统一响应格式
│  └─ log_middleware.py           # 请求日志中间件
├─ templates                      # 前端测试页面
├─ logs                           # 日志文件
├─ manage.py
└─ requirements.txt
```

**Development Process**
1. 创建虚拟环境并安装依赖
```
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```
2. 配置数据库（MySQL）
- `aipet_backend\settings.py` 中配置 `DATABASES`
3. 迁移数据库
```
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate
```
4. 启动服务
```
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```
5. 浏览器访问测试页面
- `http://127.0.0.1:8000/test/<页面名>/`

**Auth & Permission**
- 默认所有接口需要登录并携带 JWT Access Token
- 例外：注册与登录允许匿名访问
- Token 使用 `Authorization: Bearer <access_token>`
- 刷新与校验接口：
  - `POST /api/auth/token/refresh/`
  - `POST /api/auth/token/verify/`

**Common Response Format**
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
  "message": "错误说明或字段校验错误"
}
```

---

# API 文档

**1. 用户模块（/api/users/）**

**1.1 用户注册**
- 接口：`POST /api/users/createUser/`
- 认证：否（匿名允许）
- 说明：手机号注册，系统自动生成 user_name

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_phone_number | string | 是 | 中国大陆 11 位手机号，唯一 |
| user_password | string | 是 | 密码，至少 6 位 |
| user_password_confirm | string | 是 | 密码确认 |
| user_phone_code | string | 是 | 手机验证码（占位，暂不校验真实短信） |

请求示例：
```json
{
  "user_phone_number": "13800000000",
  "user_password": "123456",
  "user_password_confirm": "123456",
  "user_phone_code": "1234"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "user_a1B2c3D4",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null
  },
  "message": "注册成功"
}
```

失败响应示例：
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": {
    "user_phone_number": ["手机号已存在"]
  }
}
```

**1.2 用户登录**
- 接口：`POST /api/users/dirUser/`
- 认证：否（匿名允许）
- 说明：支持两种方式登录

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_phone_number | string | 是 | 手机号 |
| login_type | string | 是 | `password` 或 `code` |
| user_password | string | 条件 | login_type=password 时必填 |
| user_phone_code | string | 条件 | login_type=code 时必填 |

请求示例（密码登录）：
```json
{
  "user_phone_number": "13800000000",
  "login_type": "password",
  "user_password": "123456"
}
```

请求示例（验证码登录）：
```json
{
  "user_phone_number": "13800000000",
  "login_type": "code",
  "user_phone_code": "1234"
}
```

成功响应示例：
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
      "user_mail_address": null
    },
    "token": {
      "access_token": "<access_token>",
      "refresh_token": "<refresh_token>"
    }
  },
  "message": "登录成功"
}
```

失败响应示例：
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": "密码错误"
}
```

**1.3 用户信息查询**
- 接口：`GET /api/users/dirUser/`
- 认证：是
- 说明：只能查询当前登录用户本人

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | int | 否 | 与 user_phone_number 二选一 |
| user_phone_number | string | 否 | 与 user_id 二选一 |

请求示例：
```
GET /api/users/dirUser/?user_id=1
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "user_a1B2c3D4",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null
  },
  "message": "查询成功"
}
```

失败响应示例：
```json
{
  "result": "fail",
  "success": false,
  "data": null,
  "message": "无权限"
}
```

**1.4 用户信息修改**
- 接口：`PUT /api/users/updateUser/`
- 认证：是
- 说明：仅允许修改 `user_name`

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_name | string | 是 | 仅允许修改该字段 |

请求示例：
```json
{
  "user_name": "Jerry"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_id": 1,
    "user_name": "Jerry",
    "user_profile_picture": null,
    "user_phone_number": "13800000000",
    "user_mail_address": null
  },
  "message": "修改成功"
}
```

---

**2. 动作模块（/api/actions/）**

**2.1 动作创建**
- 接口：`POST /api/actions/createAction/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_action_name | string | 是 | 动作名称 |

请求示例：
```json
{
  "pet_action_name": "run"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "pet_action_id": 1,
    "pet_action_name": "run"
  },
  "message": "创建成功"
}
```

**2.2 动作查询**
- 接口：`GET /api/actions/dirAction/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_action_id | int | 是 | 动作ID |

请求示例：
```
GET /api/actions/dirAction/?pet_action_id=1
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "pet_action_id": 1,
    "pet_action_name": "run"
  },
  "message": "查询成功"
}
```

---

**3. 宠物模型模块（/api/pet-models/）**

**3.1 模型创建**
- 接口：`POST /api/pet-models/createModel/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_model_name | string | 是 | 模型名称 |

请求示例：
```json
{
  "pet_model_name": "cat"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "pet_model_id": 1,
    "pet_model_name": "cat"
  },
  "message": "创建成功"
}
```

**3.2 模型查询**
- 接口：`GET /api/pet-models/dirModel/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pet_model_id | int | 是 | 模型ID |

请求示例：
```
GET /api/pet-models/dirModel/?pet_model_id=1
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "pet_model_id": 1,
    "pet_model_name": "cat"
  },
  "message": "查询成功"
}
```

---

**4. 用户任务模块（/api/models/）**

**4.1 任务创建**
- 接口：`POST /api/models/createUserTask/`
- 认证：是
- 说明：user_id 从 Token 自动取得，不能手动传

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_name | string | 是 | 任务名称，同一用户下不可重复 |

请求示例：
```json
{
  "task_name": "我的任务"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_task_id": 1,
    "user_id": 1,
    "task_name": "我的任务"
  },
  "message": "创建成功"
}
```

**4.2 任务修改**
- 接口：`PUT /api/models/updateUserTask/`
- 认证：是
- 说明：仅允许修改 `task_name`

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| task_name | string | 是 | 新任务名，同一用户下不可重复 |

请求示例：
```json
{
  "user_task_id": 1,
  "task_name": "新的任务名"
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_task_id": 1,
    "user_id": 1,
    "task_name": "新的任务名"
  },
  "message": "修改成功"
}
```

**4.3 查询单个任务**
- 接口：`GET /api/models/dirUserTask/`
- 认证：是
- 说明：仅允许查询本人任务

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |

请求示例：
```
GET /api/models/dirUserTask/?user_task_id=1
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_task_id": 1,
    "user_id": 1,
    "task_name": "我的任务"
  },
  "message": "查询成功"
}
```

**4.4 查询当前用户任务列表**
- 接口：`GET /api/models/dirUserTaskListByUser/`
- 认证：是

输入参数：无

请求示例：
```
GET /api/models/dirUserTaskListByUser/
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": [
    {
      "user_task_id": 2,
      "user_id": 1,
      "task_name": "任务B"
    },
    {
      "user_task_id": 1,
      "user_id": 1,
      "task_name": "任务A"
    }
  ],
  "message": "查询成功"
}
```

---

**5. 任务-动作关系模块（/api/task-actions/）**

**5.1 绑定动作到任务**
- 接口：`POST /api/task-actions/bindActionToTask/`
- 认证：是
- 说明：仅允许绑定本人任务

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

请求示例：
```json
{
  "user_task_id": 1,
  "pet_action_id": 2
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "relation_id": 1,
    "user_task_id": 1,
    "pet_action_id": 2
  },
  "message": "绑定成功"
}
```

**5.2 解绑动作与任务**
- 接口：`POST /api/task-actions/unbindActionFromTask/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

请求示例：
```json
{
  "user_task_id": 1,
  "pet_action_id": 2
}
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": {
    "user_task_id": 1,
    "pet_action_id": 2
  },
  "message": "解绑成功"
}
```

**5.3 查询任务的动作列表**
- 接口：`GET /api/task-actions/dirActionListByTask/`
- 认证：是

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |

请求示例：
```
GET /api/task-actions/dirActionListByTask/?user_task_id=1
```

成功响应示例：
```json
{
  "result": "success",
  "success": true,
  "data": [
    {
      "pet_action_id": 1,
      "pet_action_name": "run"
    },
    {
      "pet_action_id": 2,
      "pet_action_name": "sit"
    }
  ],
  "message": "查询成功"
}
```

---

**6. JWT 刷新与校验**

**6.1 刷新 Token**
- 接口：`POST /api/auth/token/refresh/`

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| refresh | string | 是 | refresh_token |

请求示例：
```json
{
  "refresh": "<refresh_token>"
}
```

成功响应示例：
```json
{
  "access": "<new_access_token>"
}
```

**6.2 校验 Token**
- 接口：`POST /api/auth/token/verify/`

输入参数：
| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| token | string | 是 | access_token 或 refresh_token |

请求示例：
```json
{
  "token": "<access_token>"
}
```

成功响应示例：
```json
{}
```

## ????????

**????**
- ?????????????UserTask?????????1 ????
- ???PetAction??????????????????
- ????????????????? `user_task_action_relation` ????/???
- ?????PetModel????????????/?????????????????

**?????**
| ?? | ?? | ???? | ?? |
|---|---|---|---|
| user | user_id | user_name, user_profile_picture, user_phone_number, user_password, user_mail_address | ???????????????????? |
| user_task | user_task_id | user_id(FK), task_name | ??????????? task_name ???? |
| pet_action | pet_action_id | pet_action_name | ????? |
| pet_model | pet_model_id | pet_model_name | ????? |
| user_task_action_relation | relation_id | user_task_id(FK), pet_action_id(FK) | ??-????????????????? |

**????**
- User 1 ?? N UserTask
- UserTask N ?? N PetAction??? user_task_action_relation?
- PetModel????????? UserTask / User ?????

**?????????**
```
User (1) ???????< UserTask (N)
UserTask (N) >???< PetAction (N)
             \    (via user_task_action_relation)
PetModel ??????
```


