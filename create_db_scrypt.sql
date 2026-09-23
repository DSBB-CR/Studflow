/* ============================================================
   StudFlow
   Система взаимодействия студентов с подразделениями вуза
   PostgreSQL
   ============================================================ */


/* ============================================================
   1. EXTENSIONS
   ============================================================ */

CREATE EXTENSION IF NOT EXISTS pgcrypto;


/* ============================================================
   2. ENUM TYPES
   ============================================================ */

CREATE TYPE user_role AS ENUM (
    'student',
    'staff',
    'admin'
);

CREATE TYPE ticket_status AS ENUM (
    'new',
    'in_progress',
    'waiting_student',
    'resolved',
    'closed'
);

CREATE TYPE ticket_priority AS ENUM (
    'low',
    'normal',
    'high',
    'critical'
);

CREATE TYPE message_sender_type AS ENUM (
    'student',
    'staff',
    'system'
);

CREATE TYPE notification_type AS ENUM (
    'new_ticket',
    'new_message',
    'status_changed',
    'sla_warning',
    'sla_breached',
    'ticket_assigned',
    'appointment_created',
    'appointment_cancelled'
);

CREATE TYPE appointment_status AS ENUM (
    'scheduled',
    'completed',
    'cancelled',
    'no_show'
);


/* ============================================================
   3. USERS
   ============================================================ */

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Идентификатор пользователя в MAX
    max_user_id TEXT NOT NULL UNIQUE,

    role user_role NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_activity_at TIMESTAMPTZ
);


/* ============================================================
   4. UNIVERSITIES
   ============================================================ */

CREATE TABLE universities (
    university_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,

    short_name VARCHAR(50),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_university_name
        UNIQUE (name),

    CONSTRAINT uq_university_short_name
        UNIQUE (short_name)
);


/* ============================================================
   5. DEPARTMENTS
   ============================================================ */

CREATE TABLE departments (
    department_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    university_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_department_university
        FOREIGN KEY (university_id)
        REFERENCES universities(university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_department_name
        UNIQUE (university_id, name),

    CONSTRAINT uq_department_id_university
        UNIQUE (department_id, university_id)
);


/* ============================================================
   6. PROGRAMS
   Направления обучения
   ============================================================ */

CREATE TABLE programs (
    program_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    university_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,

    code VARCHAR(50),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_program_university
        FOREIGN KEY (university_id)
        REFERENCES universities(university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_program_name
        UNIQUE (university_id, name),

    CONSTRAINT uq_program_code
        UNIQUE (university_id, code),

    CONSTRAINT uq_program_id_university
        UNIQUE (program_id, university_id)
);


/* ============================================================
   7. STUDENT PROFILES
   ============================================================ */

CREATE TABLE student_profiles (
    student_id UUID PRIMARY KEY,

    university_id UUID NOT NULL,

    program_id UUID NOT NULL,

    full_name VARCHAR(255) NOT NULL,

    student_number VARCHAR(50),

    course SMALLINT NOT NULL,

    group_name VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_student_user
        FOREIGN KEY (student_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_student_university
        FOREIGN KEY (university_id)
        REFERENCES universities(university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_student_program
        FOREIGN KEY (program_id, university_id)
        REFERENCES programs(program_id, university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_student_number
        UNIQUE (university_id, student_number),

    CONSTRAINT chk_student_course
        CHECK (course BETWEEN 1 AND 8),

    CONSTRAINT uq_student_id_university
        UNIQUE (student_id, university_id)
);


/* ============================================================
   8. STAFF PROFILES
   ============================================================ */

CREATE TABLE staff_profiles (
    staff_id UUID PRIMARY KEY,

    full_name VARCHAR(255) NOT NULL,

    position VARCHAR(150) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_staff_user
        FOREIGN KEY (staff_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


/* ============================================================
   9. STAFF_DEPARTMENTS
   Связь сотрудников с подразделениями
   ============================================================ */

CREATE TABLE staff_departments (
    staff_id UUID NOT NULL,

    department_id UUID NOT NULL,

    can_answer BOOLEAN NOT NULL DEFAULT FALSE,

    can_search_students BOOLEAN NOT NULL DEFAULT FALSE,

    is_manager BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (staff_id, department_id),

    CONSTRAINT fk_staff_department_staff
        FOREIGN KEY (staff_id)
        REFERENCES staff_profiles(staff_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_staff_department_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


/* ============================================================
   10. TOPICS
   Темы обращений
   ============================================================ */

CREATE TABLE topics (
    topic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    department_id UUID NOT NULL,

    name VARCHAR(150) NOT NULL,

    description TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_topic_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_topic_name
        UNIQUE (department_id, name),

    CONSTRAINT uq_topic_id_department
        UNIQUE (topic_id, department_id)
);


/* ============================================================
   11. TICKETS
   Обращения студентов
   ============================================================ */

CREATE TABLE tickets (
    ticket_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    student_id UUID NOT NULL,

    department_id UUID NOT NULL,

    topic_id UUID,

    assigned_staff_id UUID,

    status ticket_status NOT NULL DEFAULT 'new',

    priority ticket_priority NOT NULL DEFAULT 'normal',

    -- Откуда получен приоритет:
    -- rules / ai / staff
    priority_source VARCHAR(30) NOT NULL DEFAULT 'rules',

    subject VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    first_response_at TIMESTAMPTZ,

    due_at TIMESTAMPTZ NOT NULL,

    resolved_at TIMESTAMPTZ,

    closed_at TIMESTAMPTZ,

    reopened_at TIMESTAMPTZ,

    CONSTRAINT fk_ticket_student
        FOREIGN KEY (student_id)
        REFERENCES student_profiles(student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_ticket_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_ticket_topic_department
        FOREIGN KEY (topic_id, department_id)
        REFERENCES topics(topic_id, department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    /*
       Сотрудник должен принадлежать именно тому
       подразделению, которому принадлежит обращение.
    */
    CONSTRAINT fk_ticket_assigned_staff
        FOREIGN KEY (assigned_staff_id, department_id)
        REFERENCES staff_departments(staff_id, department_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_ticket_priority_source
        CHECK (
            priority_source IN ('rules', 'ai', 'staff')
        ),

    CONSTRAINT chk_ticket_dates
        CHECK (
            resolved_at IS NULL
            OR resolved_at >= created_at
        ),

    CONSTRAINT chk_ticket_closed
        CHECK (
            closed_at IS NULL
            OR (
                resolved_at IS NOT NULL
                AND closed_at >= resolved_at
            )
        )
);


/* ============================================================
   12. TICKET_MESSAGES
   Сообщения внутри обращения
   ============================================================ */

CREATE TABLE ticket_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    ticket_id UUID NOT NULL,

    sender_user_id UUID,

    sender_type message_sender_type NOT NULL,

    message_text TEXT,

    -- Идентификатор сообщения в MAX
    max_message_id TEXT,

    reply_to_message_id UUID,

    is_internal BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_message_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_message_sender
        FOREIGN KEY (sender_user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_message_reply
        FOREIGN KEY (reply_to_message_id)
        REFERENCES ticket_messages(message_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_message_content
        CHECK (
            message_text IS NOT NULL
            AND length(trim(message_text)) > 0
        )
);


/* ============================================================
   13. ATTACHMENTS
   Файлы и фотографии
   ============================================================ */

CREATE TABLE attachments (
    attachment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    message_id UUID NOT NULL,

    -- Идентификатор файла в MAX
    max_file_id TEXT NOT NULL,

    file_name VARCHAR(255),

    mime_type VARCHAR(100),

    file_size BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attachment_message
        FOREIGN KEY (message_id)
        REFERENCES ticket_messages(message_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_file_size
        CHECK (
            file_size IS NULL
            OR file_size >= 0
        ),

    CONSTRAINT uq_max_file
        UNIQUE (max_file_id)
);


/* ============================================================
   14. KNOWLEDGE_ARTICLES
   База знаний
   ============================================================ */

CREATE TABLE knowledge_articles (
    article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    department_id UUID NOT NULL,

    topic_id UUID,

    title VARCHAR(255) NOT NULL,

    content TEXT NOT NULL,

    source_url TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    valid_from TIMESTAMPTZ,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_article_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_article_topic
        FOREIGN KEY (topic_id, department_id)
        REFERENCES topics(topic_id, department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


/* ============================================================
   15. SLA_POLICIES
   Правила сроков обработки
   ============================================================ */

CREATE TABLE sla_policies (
    sla_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    department_id UUID NOT NULL,

    priority ticket_priority NOT NULL,

    first_response_minutes INTEGER NOT NULL,

    resolution_minutes INTEGER NOT NULL,

    escalation_minutes INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sla_department
        FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_sla_department_priority
        UNIQUE (department_id, priority),

    CONSTRAINT chk_sla_first_response
        CHECK (first_response_minutes > 0),

    CONSTRAINT chk_sla_resolution
        CHECK (resolution_minutes > 0),

    CONSTRAINT chk_sla_escalation
        CHECK (escalation_minutes > 0),

    CONSTRAINT chk_sla_logic
        CHECK (
            escalation_minutes <= resolution_minutes
        )
);


/* ============================================================
   16. NOTIFICATIONS
   ============================================================ */

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    ticket_id UUID,

    type notification_type NOT NULL,

    payload JSONB,

    sent_at TIMESTAMPTZ,

    read_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_notification_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_notification_read
        CHECK (
            read_at IS NULL
            OR (
                sent_at IS NOT NULL
                AND read_at >= sent_at
            )
        )
);


/* ============================================================
   17. APPOINTMENTS
   Запись на личный приём
   ============================================================ */

CREATE TABLE appointments (
    appointment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    ticket_id UUID NOT NULL,

    staff_id UUID NOT NULL,

    start_at TIMESTAMPTZ NOT NULL,

    end_at TIMESTAMPTZ NOT NULL,

    status appointment_status NOT NULL DEFAULT 'scheduled',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_appointment_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_appointment_staff
        FOREIGN KEY (staff_id)
        REFERENCES staff_profiles(staff_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_appointment_time
        CHECK (end_at > start_at)
);


/* ============================================================
   18. RATINGS
   Оценка качества ответа
   ============================================================ */

CREATE TABLE ratings (
    rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    ticket_id UUID NOT NULL UNIQUE,

    score SMALLINT NOT NULL,

    comment TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rating_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_rating_score
        CHECK (score BETWEEN 1 AND 5)
);


/* ============================================================
   19. AUDIT_LOGS
   Журнал действий пользователей
   ============================================================ */

CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID,

    action VARCHAR(100) NOT NULL,

    entity_type VARCHAR(50) NOT NULL,

    entity_id UUID,

    details JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


/* ============================================================
   20. INDEXES
   ============================================================ */


/* ---------- USERS ---------- */

CREATE INDEX idx_users_role
    ON users(role);

CREATE INDEX idx_users_active
    ON users(is_active)
    WHERE is_active = TRUE;

CREATE INDEX idx_users_last_activity
    ON users(last_activity_at);


/* ---------- UNIVERSITIES ---------- */

CREATE INDEX idx_universities_active
    ON universities(is_active)
    WHERE is_active = TRUE;


/* ---------- DEPARTMENTS ---------- */

CREATE INDEX idx_departments_university
    ON departments(university_id);

CREATE INDEX idx_departments_active
    ON departments(university_id)
    WHERE is_active = TRUE;


/* ---------- PROGRAMS ---------- */

CREATE INDEX idx_programs_university
    ON programs(university_id);

CREATE INDEX idx_programs_active
    ON programs(university_id)
    WHERE is_active = TRUE;


/* ---------- STUDENTS ---------- */

CREATE INDEX idx_students_program
    ON student_profiles(program_id);

CREATE INDEX idx_students_group
    ON student_profiles(university_id, group_name);

CREATE INDEX idx_students_full_name
    ON student_profiles(full_name);


/* ---------- STAFF ---------- */

CREATE INDEX idx_staff_active
    ON staff_profiles(is_active)
    WHERE is_active = TRUE;

CREATE INDEX idx_staff_departments_department
    ON staff_departments(department_id);

CREATE INDEX idx_staff_answerable
    ON staff_departments(department_id)
    WHERE can_answer = TRUE;


/* ---------- TOPICS ---------- */

CREATE INDEX idx_topics_department
    ON topics(department_id);

CREATE INDEX idx_topics_active
    ON topics(department_id)
    WHERE is_active = TRUE;


/* ---------- TICKETS ---------- */

/*
   Очень важные индексы для очередей сотрудников.
*/

CREATE INDEX idx_tickets_student
    ON tickets(student_id, created_at DESC);

CREATE INDEX idx_tickets_department_status
    ON tickets(department_id, status);

CREATE INDEX idx_tickets_department_priority
    ON tickets(department_id, priority);

CREATE INDEX idx_tickets_assigned_staff
    ON tickets(assigned_staff_id, status);

CREATE INDEX idx_tickets_topic
    ON tickets(topic_id);

CREATE INDEX idx_tickets_due_at
    ON tickets(due_at)
    WHERE status NOT IN ('resolved', 'closed');

/*
   Очередь новых обращений.
*/

CREATE INDEX idx_tickets_new_queue
    ON tickets(department_id, priority, created_at)
    WHERE status = 'new';


/* ---------- MESSAGES ---------- */

CREATE INDEX idx_messages_ticket_created
    ON ticket_messages(ticket_id, created_at);

CREATE INDEX idx_messages_sender
    ON ticket_messages(sender_user_id);

CREATE UNIQUE INDEX idx_messages_max_id
    ON ticket_messages(max_message_id)
    WHERE max_message_id IS NOT NULL;


/* ---------- ATTACHMENTS ---------- */

CREATE INDEX idx_attachments_message
    ON attachments(message_id);


/* ---------- KNOWLEDGE BASE ---------- */

CREATE INDEX idx_articles_department
    ON knowledge_articles(department_id);

CREATE INDEX idx_articles_topic
    ON knowledge_articles(topic_id);

CREATE INDEX idx_articles_active
    ON knowledge_articles(department_id)
    WHERE is_active = TRUE;


/* ---------- SLA ---------- */

CREATE INDEX idx_sla_department
    ON sla_policies(department_id);


/* ---------- NOTIFICATIONS ---------- */

CREATE INDEX idx_notifications_user
    ON notifications(user_id, created_at DESC);

CREATE INDEX idx_notifications_unread
    ON notifications(user_id, created_at DESC)
    WHERE read_at IS NULL;


/* ---------- APPOINTMENTS ---------- */

CREATE INDEX idx_appointments_ticket
    ON appointments(ticket_id);

CREATE INDEX idx_appointments_staff_time
    ON appointments(staff_id, start_at);

CREATE INDEX idx_appointments_upcoming
    ON appointments(start_at)
    WHERE status = 'scheduled';


/* ---------- RATINGS ---------- */

CREATE INDEX idx_ratings_created
    ON ratings(created_at);


/* ---------- AUDIT ---------- */

CREATE INDEX idx_audit_user
    ON audit_logs(user_id, created_at DESC);

CREATE INDEX idx_audit_entity
    ON audit_logs(entity_type, entity_id, created_at DESC);

CREATE INDEX idx_audit_created
    ON audit_logs(created_at DESC);


/* ============================================================
   21. TRIGGER ДЛЯ updated_at
   ============================================================ */

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_knowledge_articles_updated_at
BEFORE UPDATE ON knowledge_articles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();


/* ============================================================
   22. COMMENTS
   Документирование структуры БД
   ============================================================ */

COMMENT ON DATABASE "StudFlow"
IS 'Система автоматизированного взаимодействия студентов с подразделениями вуза';

COMMENT ON TABLE users
IS 'Общие пользователи системы StudFlow';

COMMENT ON TABLE universities
IS 'Высшие учебные заведения, подключённые к StudFlow';

COMMENT ON TABLE departments
IS 'Подразделения вузов, принимающие обращения студентов';

COMMENT ON TABLE programs
IS 'Направления образовательных программ';

COMMENT ON TABLE student_profiles
IS 'Профили студентов';

COMMENT ON TABLE staff_profiles
IS 'Профили сотрудников подразделений';

COMMENT ON TABLE staff_departments
IS 'Связь сотрудников с подразделениями и их права';

COMMENT ON TABLE topics
IS 'Темы обращений студентов';

COMMENT ON TABLE tickets
IS 'Основные обращения студентов';

COMMENT ON TABLE ticket_messages
IS 'Сообщения внутри обращений';

COMMENT ON TABLE attachments
IS 'Файлы и фотографии, прикреплённые к сообщениям';

COMMENT ON TABLE knowledge_articles
IS 'Статьи базы знаний для автоматического ответа';

COMMENT ON TABLE sla_policies
IS 'Правила сроков обработки обращений';

COMMENT ON TABLE notifications
IS 'Уведомления пользователей';

COMMENT ON TABLE appointments
IS 'Записи студентов на личный приём';

COMMENT ON TABLE ratings
IS 'Оценки качества обработки обращений';

COMMENT ON TABLE audit_logs
IS 'Журнал действий пользователей и системы';