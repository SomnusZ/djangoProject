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
├── app/
│   ├── user/                   # 用户模块
│   ├── user_task/              # 用户任务模块
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
| user_task | user_task_id | user_id(FK), task_name | 用户任务表；同一用户下 task_name 不可重复 |
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

## 用户状态字段说明（user_status）

`user_status` 为 `INT` 类型，默认值 `0`，后续通过字典项配置每个值的含义，当前约定：

| 值 | 含义（暂定） |
|---|---|
| 0 | 正常 |
| 1 | 禁用 |
| 2 | 注销 |

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
      "user_status": 0
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
    "user_status": 0
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

### 4.1 创建任务

- **接口**：`POST /api/models/createUserTask/`
- **认证**：是
- **说明**：`user_id` 从 Token 自动读取，无需传参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| task_name | string | 是 | 任务名称，同一用户下不可重复 |

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": { "user_task_id": 1, "user_id": 1, "task_name": "我的任务" },
  "message": "创建成功"
}
```

### 4.2 修改任务

- **接口**：`PUT /api/models/updateUserTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| task_name | string | 是 | 新任务名 |

### 4.3 查询单个任务

- **接口**：`GET /api/models/dirUserTask/?user_task_id=1`
- **认证**：是

### 4.4 查询当前用户任务列表

- **接口**：`GET /api/models/dirUserTaskListByUser/`
- **认证**：是

**成功响应：**
```json
{
  "result": "success",
  "success": true,
  "data": [
    { "user_task_id": 2, "user_id": 1, "task_name": "任务B" },
    { "user_task_id": 1, "user_id": 1, "task_name": "任务A" }
  ],
  "message": "查询成功"
}
```

---

## 5. 任务-动作关系模块（/api/task-actions/）

### 5.1 绑定动作到任务

- **接口**：`POST /api/task-actions/bindActionToTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

### 5.2 解绑动作与任务

- **接口**：`POST /api/task-actions/unbindActionFromTask/`
- **认证**：是

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_task_id | int | 是 | 任务ID |
| pet_action_id | int | 是 | 动作ID |

### 5.3 查询任务的动作列表

- **接口**：`GET /api/task-actions/dirActionListByTask/?user_task_id=1`
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
| 货币资产模块 | `/test/wealth/` |
| 玩法任务模块 | `/test/playtask/` |
| 成就模块 | `/test/achievement/` |
| 家具模块 | `/test/furniture/` |
| 道具模块 | `/test/property/` |

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
