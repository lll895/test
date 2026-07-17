"""
企业知识库 RAG 问答系统 - 数据库迁移脚本
========================================
自动检测并添加缺失的数据表字段。

使用方法：在 server 目录下运行：
    python -c "from scripts.migrate import run; run()"
"""

import os
import sys

# 将项目目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run():
    """执行数据库迁移"""
    import pymysql
    from config import Config

    # 数据库连接配置
    db_config = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'charset': 'utf8mb4',
    }

    print(f"📦 连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # 检查 documents 表是否有 version 字段
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'version'")
        if cursor.fetchone():
            print("✅ documents.version 字段已存在，跳过")
        else:
            print("📝 添加 documents.version 字段...")
            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN `version` INT NOT NULL DEFAULT 1 COMMENT '文档版本号'
                AFTER `chunk_count`
            """)
            print("✅ documents.version 添加成功")

        # 检查 version_group_id 字段
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'version_group_id'")
        if cursor.fetchone():
            print("✅ documents.version_group_id 字段已存在，跳过")
        else:
            print("📝 添加 documents.version_group_id 字段...")
            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN `version_group_id` VARCHAR(64) DEFAULT NULL COMMENT '版本分组ID'
                AFTER `version`
            """)
            print("✅ documents.version_group_id 添加成功")

        # 检查 change_note 字段
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'change_note'")
        if cursor.fetchone():
            print("✅ documents.change_note 字段已存在，跳过")
        else:
            print("📝 添加 documents.change_note 字段...")
            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN `change_note` VARCHAR(500) DEFAULT NULL COMMENT '版本变更说明'
                AFTER `version_group_id`
            """)
            print("✅ documents.change_note 添加成功")

        # 创建 password_reset_tokens 表（如果不存在）
        cursor.execute("SHOW TABLES LIKE 'password_reset_tokens'")
        if cursor.fetchone():
            print("✅ password_reset_tokens 表已存在，跳过")
        else:
            print("📝 创建 password_reset_tokens 表...")
            cursor.execute("""
                CREATE TABLE `password_reset_tokens` (
                    `id` INT AUTO_INCREMENT COMMENT '主键ID',
                    `user_id` INT NOT NULL COMMENT '用户ID',
                    `token` VARCHAR(64) NOT NULL COMMENT '重置令牌',
                    `expires_at` DATETIME NOT NULL COMMENT '过期时间',
                    `used` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已使用',
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `uk_token` (`token`),
                    KEY `idx_user_id` (`user_id`),
                    CONSTRAINT `fk_prt_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='密码重置令牌表'
            """)
            print("✅ password_reset_tokens 表创建成功")

        # 添加 documents 表的版本字段
        cursor.execute("SHOW COLUMNS FROM documents LIKE 'version'")
        if cursor.fetchone():
            print("✅ documents.version 字段已存在，跳过")
        else:
            print("📝 添加 documents.version 字段...")
            cursor.execute("ALTER TABLE documents ADD COLUMN `version` INT NOT NULL DEFAULT 1 AFTER `chunk_count`")
            cursor.execute("ALTER TABLE documents ADD COLUMN `version_group_id` VARCHAR(64) DEFAULT NULL AFTER `version`")
            cursor.execute("ALTER TABLE documents ADD COLUMN `change_note` VARCHAR(500) DEFAULT NULL AFTER `version_group_id`")
            cursor.execute("ALTER TABLE documents ADD INDEX `idx_version_group_id` (`version_group_id`)")
            print("✅ documents 版本字段添加成功")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 数据库迁移完成！")

    except pymysql.err.OperationalError as e:
        print(f"\n❌ 数据库连接失败: {e}")
        print("   请检查 MySQL 服务是否运行，以及 config.py 中的数据库配置")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run()
