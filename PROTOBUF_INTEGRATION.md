# Protobuf 联调说明（当前项目）

## 1. 当前支持范围
- 当前项目已支持 **响应体** 按内容协商返回 Protobuf。
- 当前项目默认仍返回 JSON（向后兼容）。
- 当前项目暂未启用请求体 Protobuf 解析（即：请求 body 仍建议发送 JSON）。
- `user` 模块已接入强类型 message：
1. `UserResponse`：用于 `createUser` / `updateUser` / `dirUser(GET)`
2. `UserLoginResponse`：用于 `dirUser(POST)`
- 其它模块仍走通用壳 `ApiEnvelope`。

## 2. 生效条件
- 想要 Protobuf 响应时，请在请求头中加入：
```http
Accept: application/x-protobuf
```
- 不加该请求头时，默认返回 JSON。

## 3. 依赖要求
- 后端运行环境需安装：
```powershell
.\venv\Scripts\python.exe -m pip install protobuf==5.29.3
```

## 4. 快速验证（curl）
### 4.1 获取 JSON（默认）
```bash
curl -X GET "http://127.0.0.1:8000/api/users/dirUser/?user_id=1" ^
  -H "Authorization: Bearer <access_token>"
```

### 4.2 获取 Protobuf（二进制）
```bash
curl -X GET "http://127.0.0.1:8000/api/users/dirUser/?user_id=1" ^
  -H "Authorization: Bearer <access_token>" ^
  -H "Accept: application/x-protobuf" ^
  --output user_dir_user.pb
```

说明：
- `user_dir_user.pb` 是二进制文件，不可直接当文本阅读。
- 可用 Python 脚本按 `ApiEnvelope` 结构反序列化查看。

## 5. Python 客户端示例
```python
import requests
from app.proto.common_pb2 import ApiEnvelope

url = "http://127.0.0.1:8000/api/users/dirUser/?user_id=1"
headers = {
    "Authorization": "Bearer <access_token>",
    "Accept": "application/x-protobuf",
}

resp = requests.get(url, headers=headers, timeout=10)
resp.raise_for_status()

msg = ApiEnvelope()
msg.ParseFromString(resp.content)

print("result:", msg.result)
print("success:", msg.success)
print("data:", msg.data)
print("message:", msg.message)
```

## 6. 前端 Fetch 示例
```javascript
async function queryUserAsProtobuf(accessToken, userId) {
  const resp = await fetch(`/api/users/dirUser/?user_id=${userId}`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${accessToken}`,
      "Accept": "application/x-protobuf",
    },
  });

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }

  // 当前拿到的是二进制 ArrayBuffer
  const buf = await resp.arrayBuffer();
  return buf;
}
```

说明：
- 浏览器端如果要“解码 protobuf 为对象”，需要引入 protobuf 解码库（例如 protobuf.js），并提供相同的 `.proto` 定义。
- 如果前端暂不做解码，可先验证二进制长度、状态码与响应头。

## 7. 响应结构说明（统一壳）
- 当前 Protobuf 使用统一壳 `ApiEnvelope`，字段与现有 JSON 响应保持一致：
1. `result`：`success` / `fail`
2. `success`：`true` / `false`
3. `data`：动态对象（`google.protobuf.Value`）
4. `message`：动态内容（字符串或结构化错误）

## 8. 常见问题
### 8.1 为什么看到乱码？
- Protobuf 是二进制，不是文本。
- 请用 protobuf 解码后再查看。

### 8.2 为什么我发 protobuf 请求体不生效？
- 当前版本未启用 `ProtobufParser`。
- 现阶段仅支持“响应 protobuf”。

### 8.3 怎么确认后端确实返回 protobuf？
- 检查响应头：
```http
Content-Type: application/x-protobuf
```

## 9. 建议的下一步
1. 先在 `user` 模块新增强类型 message（替代全部 `Value` 的动态字段）。
2. 再按优先级把 `user_task`、`pet_action` 逐步升级为强类型 message。
3. 最后再考虑启用 `ProtobufParser`，实现请求和响应全链路 protobuf。
