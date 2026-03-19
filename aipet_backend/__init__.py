"""
项目初始化文件。
用于可选地启用 PyMySQL 作为 MySQL 驱动。
"""

try:
    import pymysql  # type: ignore

    # 使用 PyMySQL 替代 MySQLdb
    pymysql.install_as_MySQLdb()
except Exception:
    # 未安装 PyMySQL 时忽略，保持默认行为
    pass
