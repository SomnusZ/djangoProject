# AIPet Backend 项目开发纪要（学习记录与锚点）

> 说明：本纪要基于我们实际的开发过程、日志与对话整理，旨在作为学习总结与后续完善的锚点。
> 时间信息以日志中可见时间为准（如 2026-03-30 ～ 2026-04-05）。若后续有新增功能可继续追加。

---

## 1. 项目目标与范围
- 目标：构建一个完整可运行的 Django + DRF + MySQL 后端项目，支持用户、任务、动作、模型与关联关系。
- 约束：接口使用 RESTful 风格；响应统一 success/fail；强制登录（除注册/登录）。
- 前端联调：提供简单 HTML 页面用于注册、登录、查询、更新与业务联调。

---

## 2. 初始化阶段
**2.1 环境准备**
- Python 3.11
- Django 5.2.12 / DRF 3.16.1 / MySQL
- 依赖在 `requirements.txt` 中统一管理。

**2.2 基础工程搭建**
- 项目根目录：`F:\workspace_Pycharm_git\djangoProject`
- 主工程：`aipet_backend`
- 业务应用：`app` 目录下多个子模块

**2.3 数据库配置**
- 使用 MySQL 数据库 `aipetdb`
- 在 `aipet_backend\settings.py` 中配置连接参数

---

## 3. 用户模块构建
**3.1 用户模型设计**
- `user_id` 主键
- `user_phone_number` 手机号（唯一）
- `user_password` 密码（哈希存储）
- `user_name` 用户名（自动生成）
- `user_profile_picture` 头像字段
- `user_mail_address` 邮箱（弃用但保留字段）

**3.2 注册逻辑**
- 仅支持手机号注册
- 必填：手机号、密码、密码确认、手机验证码（占位）
- 注册成功自动生成用户名：`user_` + 随机字母数字
- 手机号唯一性校验（数据库唯一约束 + 序列化器校验）

**3.3 登录逻辑（双模式）**
- 手机号 + 密码
- 手机号 + 验证码（占位校验）

**3.4 用户查询/更新**
- 查询：仅允许查询本人信息（权限校验）
- 更新：仅允许修改 `user_name`

---

## 4. 认证与权限演进
**4.1 JWT 引入**
- 使用 `djangorestframework-simplejwt`
- 登录成功返回 access_token + refresh_token

**4.2 强制登录**
- 默认全局需要 Token
- 仅注册/登录允许匿名访问

**4.3 归属权限控制**
- 统一封装权限逻辑：
  - `OwnedQuerySetMixin`
  - `OwnedObjectMixin`
  - `IsOwnerPermission`
- 目的：避免用户修改/查询其他用户的数据

**4.4 常见权限问题与修复**
- Token 对象必须能识别自定义 `user_id`
- 修复 `user_id` 不存在导致的 Token 解析异常
- 避免在登录接口中强制 Token 校验

---

## 5. 业务模块扩展
**5.1 pet_action 动作字典**
- 新增动作
- 查询动作

**5.2 pet_model 模型字典**
- 新增模型
- 查询模型

**5.3 user_task 用户任务**
- 用户创建任务（自动绑定 user_id）
- 任务名在同一用户下不可重复
- 更新任务：仅允许修改 `task_name`
- 查询单个任务 / 查询本人任务列表

**5.4 user_task_action_relation 任务-动作关系**
- 独立映射表（多对多）
- 绑定 / 解绑动作
- 按任务查询动作列表

---

## 6. 前端测试页面构建
**6.1 初始测试页面**
- 注册 / 登录 / 查询 / 修改

**6.2 统一风格**
- 页面统一布局、响应区、按钮样式
- 增加 localStorage 自动读取 token

**6.3 业务测试页面扩展**
- pet_action 创建/查询
- pet_model 创建/查询
- user_task 创建/查询/更新/列表
- relation 绑定/解绑/查询

---

## 7. 报错与修复过程（关键记录）
**7.1 数据库表不存在**
- 报错：`Table 'xxx' doesn't exist`
- 处理：`makemigrations` + `migrate`

**7.2 默认 auth_user 表**
- 原因：未使用自定义 User 作为 Django Auth 模型
- 处理：保留默认 auth_user，不影响自定义 user 表

**7.3 JWT 解析异常**
- 报错：`AttributeError: 'User' object has no attribute 'id'`
- 原因：SimpleJWT 默认主键字段为 `id`
- 修复：设置 `USER_ID_FIELD = user_id` 并自定义认证类

**7.4 权限失效问题**
- 原因：用户查询接口未正确校验归属
- 修复：统一权限校验（owner 验证）

**7.5 编码乱码问题（高频）**
- 报错：`UnicodeDecodeError` 或页面显示 `???`
- 处理：统一全项目文件 UTF-8，HTML 输出带 BOM

**7.6 迁移与重复数据冲突**
- 报错：`Duplicate entry` / `Table already exists`
- 处理：清理测试数据、重新迁移

---

## 8. 工程化完善
**8.1 统一响应格式**
- 所有接口输出：`success/fail` 结构

**8.2 请求日志中间件**
- 输出请求方法、路径、耗时、用户 ID
- 文件日志 + 控制台日志

**8.3 接口文档体系**
- `PROJECT_DOC.md` + `PROJECT_DOC.html`
- 统一接口输入/输出示例

---

## 9. 当前状态总结
- 模型与业务表结构稳定
- JWT 登录可用
- 权限校验可用
- 前端测试页面齐全
- 文档已生成

---

## 10. 后续可继续完善方向（项目锚点）
**10.1 权限细化**
- 不同角色/权限等级
- 资源级别的细粒度控制

**10.2 日志增强**
- 增加 request_id
- 记录异常堆栈
- 统一错误追踪

**10.3 测试体系**
- 单元测试（model/serializer/view）
- 接口测试（pytest + API 测试）

**10.4 安全与稳定性**
- 验证码真实接入
- Token 黑名单机制
- 防刷机制

**10.5 文档自动化**
- 自动生成 Swagger / OpenAPI
- 前端联调用例清单

---

## 11. 个人学习总结（建议记录点）
- Django/DRF 结构理解
- 权限与认证的演进过程
- 数据库迁移与错误修复经验
- UTF-8 编码问题的排查与修复
- 前后端联调流程

---

> 该文档建议随项目持续更新，每次新增功能都追加「新增/变更」小节，形成完整迭代记录。
