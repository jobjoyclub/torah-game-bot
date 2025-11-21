-- ===================================================================
-- TORAH BOT NEWSLETTER DATABASE SCHEMA (Variant A Enhanced)
-- ===================================================================

-- Основная таблица пользователей с полной информацией
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction TIMESTAMPTZ DEFAULT NOW(),
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    -- Статистика активности пользователя
    total_wisdom_requests INTEGER DEFAULT 0,
    total_quiz_attempts INTEGER DEFAULT 0,
    last_wisdom_topic VARCHAR(200),
    -- Для аналитики
    user_data JSONB, -- Дополнительная информация от Telegram
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Подписки на рассылку (расширенные)
CREATE TABLE newsletter_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_user_id) ON DELETE CASCADE,
    -- Настройки подписки
    is_active BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) DEFAULT 'English',
    timezone VARCHAR(50) DEFAULT 'UTC',
    delivery_time TIME DEFAULT '09:00:00', -- Предпочтительное время
    -- Типы подписок
    daily_wisdom BOOLEAN DEFAULT TRUE,
    special_events BOOLEAN DEFAULT TRUE,
    -- Временные метки
    subscribed_at TIMESTAMPTZ DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,
    last_delivery TIMESTAMPTZ,
    -- Статистика
    total_deliveries INTEGER DEFAULT 0,
    total_opens INTEGER DEFAULT 0,
    last_open TIMESTAMPTZ
);

-- Контент для рассылок
CREATE TABLE newsletter_broadcasts (
    id BIGSERIAL PRIMARY KEY,
    broadcast_date DATE NOT NULL UNIQUE,
    -- Контент на разных языках (JSON структура)
    wisdom_content JSONB NOT NULL, -- {"en": {"text": "...", "topic": "...", "references": "..."}}
    image_url TEXT,
    -- Статус рассылки
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'ready', 'sending', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    -- Статистика
    total_recipients INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    -- Метаданные
    created_by VARCHAR(100), -- Админ который создал
    notes TEXT
);

-- Лог доставки сообщений
CREATE TABLE delivery_log (
    id BIGSERIAL PRIMARY KEY,
    broadcast_id BIGINT REFERENCES newsletter_broadcasts(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(telegram_user_id) ON DELETE CASCADE,
    -- Статус доставки
    status VARCHAR(20) NOT NULL, -- 'pending', 'sent', 'failed', 'blocked', 'opened'
    attempt_count INTEGER DEFAULT 0,
    -- Временные метки
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    -- Ошибки
    error_message TEXT,
    telegram_message_id INTEGER,
    -- Дополнительная информация
    delivery_metadata JSONB -- Информация о доставке, устройстве и т.д.
);

-- Админские пользователи и права доступа
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin', -- 'admin', 'moderator', 'viewer'
    permissions JSONB, -- {"can_send_broadcasts": true, "can_view_analytics": true}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Тестовые рассылки для админов
CREATE TABLE test_broadcasts (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT REFERENCES admin_users(telegram_user_id),
    test_content JSONB NOT NULL, -- Тестовый контент
    test_image_url TEXT,
    target_languages TEXT[], -- Языки для тестирования
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'sent'
    notes TEXT
);

-- ===================================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ===================================================================

-- Основные индексы для пользователей
CREATE INDEX idx_users_telegram_id ON users(telegram_user_id);
CREATE INDEX idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX idx_users_last_interaction ON users(last_interaction DESC);
CREATE INDEX idx_users_created ON users(created_at DESC);

-- Индексы для подписок
CREATE INDEX idx_subscriptions_user_active ON newsletter_subscriptions(user_id, is_active);
CREATE INDEX idx_subscriptions_delivery_time ON newsletter_subscriptions(delivery_time, timezone) WHERE is_active = TRUE;
CREATE INDEX idx_subscriptions_language ON newsletter_subscriptions(language) WHERE is_active = TRUE;

-- Индексы для рассылок
CREATE INDEX idx_broadcasts_date ON newsletter_broadcasts(broadcast_date DESC);
CREATE INDEX idx_broadcasts_status ON newsletter_broadcasts(status, scheduled_at);
CREATE INDEX idx_broadcasts_created ON newsletter_broadcasts(created_at DESC);

-- Индексы для логов доставки
CREATE INDEX idx_delivery_log_broadcast ON delivery_log(broadcast_id, status);
CREATE INDEX idx_delivery_log_user ON delivery_log(user_id, delivered_at DESC);
CREATE INDEX idx_delivery_log_status_scheduled ON delivery_log(status, scheduled_at) WHERE status = 'pending';

-- Индексы для админов
CREATE INDEX idx_admin_users_telegram_id ON admin_users(telegram_user_id);
CREATE INDEX idx_admin_users_role ON admin_users(role, is_active);

-- ===================================================================
-- ФУНКЦИИ И ТРИГГЕРЫ
-- ===================================================================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at в users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для автоматического подсчета статистики рассылок
CREATE OR REPLACE FUNCTION update_broadcast_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'sent' AND OLD.status != 'sent' THEN
        UPDATE newsletter_broadcasts 
        SET successful_deliveries = successful_deliveries + 1
        WHERE id = NEW.broadcast_id;
    ELSIF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        UPDATE newsletter_broadcasts 
        SET failed_deliveries = failed_deliveries + 1
        WHERE id = NEW.broadcast_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для обновления статистики рассылок
CREATE TRIGGER update_broadcast_delivery_stats
    AFTER UPDATE ON delivery_log
    FOR EACH ROW EXECUTE FUNCTION update_broadcast_stats();

-- ===================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ===================================================================

-- Добавляем админского пользователя @torah_support для тестирования
INSERT INTO admin_users (telegram_user_id, username, role, permissions) VALUES 
(6630727156, 'torah_support', 'admin', 
 '{"can_send_broadcasts": true, "can_view_analytics": true, "can_test_broadcasts": true, "can_manage_users": true}');

-- Создаем тестовую запись для первой рассылки
INSERT INTO newsletter_broadcasts (broadcast_date, wisdom_content, status, created_by) VALUES
(CURRENT_DATE, '{}', 'draft', 'torah_support');

-- ===================================================================
-- ПОЛЕЗНЫЕ ВЬЮХИ ДЛЯ АНАЛИТИКИ
-- ===================================================================

-- Вьюха активных подписчиков по языкам
CREATE VIEW active_subscribers_by_language AS
SELECT 
    ns.language,
    COUNT(*) as subscriber_count,
    COUNT(*) FILTER (WHERE u.last_interaction > NOW() - INTERVAL '30 days') as active_users_30d,
    COUNT(*) FILTER (WHERE u.last_interaction > NOW() - INTERVAL '7 days') as active_users_7d
FROM newsletter_subscriptions ns
JOIN users u ON u.telegram_user_id = ns.user_id
WHERE ns.is_active = TRUE
GROUP BY ns.language
ORDER BY subscriber_count DESC;

-- Вьюха статистики рассылок
CREATE VIEW broadcast_statistics AS
SELECT 
    nb.id,
    nb.broadcast_date,
    nb.status,
    nb.total_recipients,
    nb.successful_deliveries,
    nb.failed_deliveries,
    CASE 
        WHEN nb.total_recipients > 0 THEN 
            ROUND((nb.successful_deliveries::DECIMAL / nb.total_recipients * 100), 2)
        ELSE 0 
    END as delivery_rate_percent,
    COUNT(dl.opened_at) as total_opens,
    CASE 
        WHEN nb.successful_deliveries > 0 THEN 
            ROUND((COUNT(dl.opened_at)::DECIMAL / nb.successful_deliveries * 100), 2)
        ELSE 0 
    END as open_rate_percent
FROM newsletter_broadcasts nb
LEFT JOIN delivery_log dl ON nb.id = dl.broadcast_id
GROUP BY nb.id, nb.broadcast_date, nb.status, nb.total_recipients, 
         nb.successful_deliveries, nb.failed_deliveries
ORDER BY nb.broadcast_date DESC;