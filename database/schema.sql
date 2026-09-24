-- =============================================================================
-- AI-Powered Job & Internship Intelligence Platform
-- MySQL 8.0 Reference Database Schema
-- Character Set: utf8mb4, Collation: utf8mb4_unicode_ci
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `ai_job_portal_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ai_job_portal_db`;

-- 1. Users Table (Dual Role: Student / Recruiter / Admin)
CREATE TABLE IF NOT EXISTS `accounts_user` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `password` VARCHAR(128) NOT NULL,
    `last_login` DATETIME(6) NULL,
    `is_superuser` TINYINT(1) NOT NULL DEFAULT 0,
    `username` VARCHAR(150) NOT NULL UNIQUE,
    `first_name` VARCHAR(150) NOT NULL DEFAULT '',
    `last_name` VARCHAR(150) NOT NULL DEFAULT '',
    `email` VARCHAR(254) NOT NULL,
    `is_staff` TINYINT(1) NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `date_joined` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `role` VARCHAR(20) NOT NULL DEFAULT 'student',
    `phone` VARCHAR(20) NOT NULL DEFAULT '',
    `profile_picture` VARCHAR(100) NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX `idx_accounts_user_role` (`role`),
    INDEX `idx_accounts_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Companies Table
CREATE TABLE IF NOT EXISTS `companies_company` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(200) NOT NULL UNIQUE,
    `slug` VARCHAR(220) NOT NULL UNIQUE,
    `website` VARCHAR(200) NOT NULL DEFAULT '',
    `industry` VARCHAR(120) NOT NULL DEFAULT 'Technology',
    `company_size` VARCHAR(20) NOT NULL DEFAULT '51-200',
    `location` VARCHAR(200) NOT NULL DEFAULT '',
    `description` LONGTEXT NOT NULL,
    `logo` VARCHAR(100) NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX `idx_companies_industry` (`industry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Recruiter Profiles Table
CREATE TABLE IF NOT EXISTS `recruiters_recruiterprofile` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL UNIQUE,
    `company_id` BIGINT NULL,
    `designation` VARCHAR(150) NOT NULL DEFAULT 'Talent Acquisition Lead',
    `department` VARCHAR(120) NOT NULL DEFAULT 'Human Resources',
    `linkedin_url` VARCHAR(200) NOT NULL DEFAULT '',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`company_id`) REFERENCES `companies_company` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Student Profiles Table (Resume Text & AI Insights)
CREATE TABLE IF NOT EXISTS `students_studentprofile` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL UNIQUE,
    `headline` VARCHAR(200) NOT NULL DEFAULT '',
    `bio` LONGTEXT NOT NULL,
    `degree` VARCHAR(150) NOT NULL DEFAULT '',
    `institution` VARCHAR(200) NOT NULL DEFAULT '',
    `graduation_year` INT NULL,
    `cgpa` DECIMAL(4, 2) NULL,
    `location` VARCHAR(150) NOT NULL DEFAULT '',
    `github_url` VARCHAR(200) NOT NULL DEFAULT '',
    `linkedin_url` VARCHAR(200) NOT NULL DEFAULT '',
    `portfolio_url` VARCHAR(200) NOT NULL DEFAULT '',
    `skills` LONGTEXT NOT NULL,
    `resume_file` VARCHAR(100) NULL,
    `parsed_resume_text` LONGTEXT NOT NULL,
    `extracted_skills` JSON NOT NULL,
    `resume_sections` JSON NOT NULL,
    `ats_score` INT NOT NULL DEFAULT 0,
    `ats_feedback` JSON NOT NULL,
    `preferred_job_titles` VARCHAR(255) NOT NULL DEFAULT '',
    `preferred_locations` VARCHAR(255) NOT NULL DEFAULT '',
    `expected_salary` DECIMAL(12, 2) NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    INDEX `idx_students_ats_score` (`ats_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Jobs & Internships Table
CREATE TABLE IF NOT EXISTS `jobs_job` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `job_type` VARCHAR(20) NOT NULL DEFAULT 'full_time',
    `work_mode` VARCHAR(20) NOT NULL DEFAULT 'remote',
    `location` VARCHAR(150) NOT NULL DEFAULT '',
    `experience_level` VARCHAR(20) NOT NULL DEFAULT 'entry',
    `min_experience_years` INT NOT NULL DEFAULT 0,
    `salary_min` DECIMAL(12, 2) NULL,
    `salary_max` DECIMAL(12, 2) NULL,
    `is_salary_negotiable` TINYINT(1) NOT NULL DEFAULT 1,
    `description` LONGTEXT NOT NULL,
    `responsibilities` LONGTEXT NOT NULL,
    `requirements` LONGTEXT NOT NULL,
    `required_skills` JSON NOT NULL,
    `preferred_skills` JSON NOT NULL,
    `ai_summary` LONGTEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'active',
    `deadline` DATE NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `company_id` BIGINT NOT NULL,
    `recruiter_id` BIGINT NOT NULL,
    FOREIGN KEY (`company_id`) REFERENCES `companies_company` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`recruiter_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    INDEX `idx_jobs_status` (`status`),
    INDEX `idx_jobs_type` (`job_type`),
    INDEX `idx_jobs_work_mode` (`work_mode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Applications Table (Snapshot AI Match Scores)
CREATE TABLE IF NOT EXISTS `applications_application` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `cover_letter` LONGTEXT NOT NULL,
    `resume_file` VARCHAR(100) NULL,
    `overall_match_score` DOUBLE NOT NULL DEFAULT 0,
    `skill_match_score` DOUBLE NOT NULL DEFAULT 0,
    `semantic_match_score` DOUBLE NOT NULL DEFAULT 0,
    `experience_match_score` DOUBLE NOT NULL DEFAULT 0,
    `match_explanation` JSON NOT NULL,
    `status` VARCHAR(25) NOT NULL DEFAULT 'applied',
    `recruiter_notes` LONGTEXT NOT NULL,
    `applied_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `job_id` BIGINT NOT NULL,
    `student_id` BIGINT NOT NULL,
    UNIQUE KEY `unique_job_application` (`job_id`, `student_id`),
    FOREIGN KEY (`job_id`) REFERENCES `jobs_job` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`student_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    INDEX `idx_applications_status` (`status`),
    INDEX `idx_applications_score` (`overall_match_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

