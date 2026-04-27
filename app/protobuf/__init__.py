# app/protobuf/  —  DRF Protobuf 集成层
#
# 职责：将 protobuf 序列化/反序列化能力接入 DRF 的内容协商机制。
# 与 app/proto/（Schema 定义层）分离，各司其职。
#
# 对外暴露：
#   - ProtobufParser   : 处理 Content-Type: application/x-protobuf 的请求体
#   - ProtobufRenderer : 处理 Accept: application/x-protobuf 的响应序列化
#
# settings.py 中的引用路径：
#   'app.protobuf.renderer.ProtobufRenderer'
#   'app.protobuf.parser.ProtobufParser'
