-- ============================================================================
-- 企业知识库 RAG 问答系统 - v2.0 数据库迁移脚本
-- 说明：从 v1.0 升级到 v2.0 需要执行的变更
-- ============================================================================

-- 1. 文档表新增版本管理字段
ALTER TABLE `documents`
    ADD COLUMN `version` INT NOT NULL DEFAULT 1 COMMENT '文档版本号' AFTER `chunk_count`,
    ADD COLUMN `version_group_id` VARCHAR(64) DEFAULT NULL COMMENT '版本分组ID（同组文档共享此ID）' AFTER `version`,
    ADD COLUMN `change_note` VARCHAR(500) DEFAULT NULL COMMENT '版本变更说明' AFTER `version_group_id`,
    ADD INDEX `idx_version_group_id` (`version_group_id`);

-- 2. 用户表新增密码重置字段
ALTER TABLE `users`
    ADD COLUMN `reset_token` VARCHAR(64) DEFAULT NULL COMMENT '密码重置令牌' AFTER `avatar`,
    ADD COLUMN `reset_token_expires` DATETIME DEFAULT NULL COMMENT '重置令牌过期时间' AFTER `reset_token`,
    ADD INDEX `idx_reset_token` (`reset_token`);
