-- ============================================================================
-- 企业知识库 RAG 问答系统 - 数据库初始化脚本
-- 数据库: dbenterprise
-- 说明: 创建系统所需的全部数据表
-- ============================================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS dbenterprise DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE dbenterprise;

-- ============================================================================
-- 用户表: 存储管理员和普通用户信息
-- ============================================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT COMMENT '用户ID，主键自增',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名，唯一',
    `password` VARCHAR(64) NOT NULL COMMENT '密码（MD5加密）',
    `real_name` VARCHAR(100) DEFAULT NULL COMMENT '真实姓名',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱地址',
    `role` ENUM('admin', 'user') NOT NULL DEFAULT 'user' COMMENT '角色：admin=管理员，user=普通用户',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1=启用，0=禁用',
    `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
    `last_login` DATETIME DEFAULT NULL COMMENT '最后登录时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_role` (`role`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================================
-- 文档分类表: 对知识库文档进行分类管理
-- ============================================================================
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT COMMENT '分类ID，主键自增',
    `name` VARCHAR(100) NOT NULL COMMENT '分类名称',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '分类描述',
    `parent_id` INT DEFAULT NULL COMMENT '父分类ID，支持多级分类',
    `sort_order` INT DEFAULT 0 COMMENT '排序序号',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_parent_id` (`parent_id`),
    CONSTRAINT `fk_category_parent` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档分类表';

-- ============================================================================
-- 文档表: 存储上传的知识文档元信息
-- ============================================================================
DROP TABLE IF EXISTS `documents`;
CREATE TABLE `documents` (
    `id` INT AUTO_INCREMENT COMMENT '文档ID，主键自增',
    `title` VARCHAR(255) NOT NULL COMMENT '文档标题',
    `file_name` VARCHAR(255) NOT NULL COMMENT '原始文件名',
    `file_path` VARCHAR(500) DEFAULT NULL COMMENT '文件存储路径',
    `file_size` BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    `file_type` VARCHAR(50) DEFAULT NULL COMMENT '文件类型（pdf/txt/docx/md）',
    `content_text` LONGTEXT COMMENT '提取的文本内容（用于向量化）',
    `summary` TEXT COMMENT '文档摘要',
    `category_id` INT DEFAULT NULL COMMENT '所属分类ID',
    `uploaded_by` INT NOT NULL COMMENT '上传者用户ID',
    `status` ENUM('processing', 'ready', 'failed') NOT NULL DEFAULT 'processing' COMMENT '处理状态：processing=处理中，ready=已完成，failed=失败',
    `chunk_count` INT DEFAULT 0 COMMENT '文本块数量',
    `error_message` TEXT COMMENT '处理失败时的错误信息',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_uploaded_by` (`uploaded_by`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_doc_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_doc_uploader` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识文档表';

-- ============================================================================
-- 文档块表: 存储文档切分后的文本块（与 Chroma 向量对应）
-- ============================================================================
DROP TABLE IF EXISTS `document_chunks`;
CREATE TABLE `document_chunks` (
    `id` INT AUTO_INCREMENT COMMENT '块ID，主键自增',
    `document_id` INT NOT NULL COMMENT '所属文档ID',
    `chunk_index` INT NOT NULL COMMENT '块序号（文档内顺序）',
    `content` TEXT NOT NULL COMMENT '文本块内容',
    `token_count` INT DEFAULT 0 COMMENT 'Token数量估算',
    `vector_id` VARCHAR(100) DEFAULT NULL COMMENT 'Chroma向量数据库中对应的ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_document_id` (`document_id`),
    KEY `idx_vector_id` (`vector_id`),
    CONSTRAINT `fk_chunk_document` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档文本块表';

-- ============================================================================
-- 问答记录表: 存储用户的提问和系统回答
-- ============================================================================
DROP TABLE IF EXISTS `qa_logs`;
CREATE TABLE `qa_logs` (
    `id` INT AUTO_INCREMENT COMMENT '记录ID，主键自增',
    `user_id` INT NOT NULL COMMENT '提问用户ID',
    `question` TEXT NOT NULL COMMENT '用户问题',
    `answer` LONGTEXT COMMENT '系统回答',
    `sources` JSON COMMENT '回答引用的来源文档信息（JSON数组）',
    `model_used` VARCHAR(100) DEFAULT NULL COMMENT '使用的模型名称',
    `embedding_model` VARCHAR(100) DEFAULT NULL COMMENT '使用的嵌入模型名称',
    `chunks_retrieved` INT DEFAULT 0 COMMENT '检索到的文档块数量',
    `tokens_used` INT DEFAULT 0 COMMENT '消耗的Token数量',
    `cost_time_ms` INT DEFAULT 0 COMMENT '回答耗时（毫秒）',
    `feedback` TINYINT DEFAULT NULL COMMENT '用户反馈：1=有用，0=无用，-1=未评价',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_created_at` (`created_at`),
    FULLTEXT KEY `ft_question` (`question`),
    CONSTRAINT `fk_qa_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答记录表';

-- ============================================================================
-- 系统公告表: 管理员发布系统公告
-- ============================================================================
DROP TABLE IF EXISTS `announcements`;
CREATE TABLE `announcements` (
    `id` INT AUTO_INCREMENT COMMENT '公告ID，主键自增',
    `title` VARCHAR(255) NOT NULL COMMENT '公告标题',
    `content` TEXT NOT NULL COMMENT '公告内容',
    `priority` ENUM('low', 'normal', 'high') NOT NULL DEFAULT 'normal' COMMENT '优先级',
    `published_by` INT NOT NULL COMMENT '发布者ID',
    `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否生效',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_published_by` (`published_by`),
    KEY `idx_is_active` (`is_active`),
    CONSTRAINT `fk_announcement_publisher` FOREIGN KEY (`published_by`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统公告表';
