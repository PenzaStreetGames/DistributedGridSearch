CREATE TABLE node_status (
    node_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE node_role (
    node_role_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE node (
    node_uid VARCHAR(36) PRIMARY KEY, -- uuid
    ipv4_address VARCHAR(21), -- 255.255.255.255:65535
    last_ping VARCHAR(23), -- YYYY-MM-DD HH:MM:SS.SSS
    node_role_id INT,
    node_status_id INT,
    FOREIGN KEY (node_status_id) REFERENCES node_status(node_status_id),
    FOREIGN KEY (node_role_id) REFERENCES node_role(node_role_id)
);

CREATE TABLE task_type (
    task_type_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE task_status (
    task_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE task (
    task_uid VARCHAR(36) PRIMARY KEY, -- uuid
    task_type_id INT,
    creator_uid VARCHAR(36),
    task_status_id INT,
    created_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    finished_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    params TEXT,
    result TEXT NULL,
    FOREIGN KEY (task_type_id) REFERENCES task_type(task_type_id),
    FOREIGN KEY (task_status_id) REFERENCES task_status(task_status_id),
    FOREIGN KEY (creator_uid) REFERENCES node(node_uid)
);

CREATE TABLE subtask_type (
    subtask_type_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE subtask_status (
    subtask_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE subtask (
    subtask_uid VARCHAR(36) PRIMARY KEY, -- uuid
    task_uid VARCHAR(36),
    subtask_type_id INT,
    executor_uid VARCHAR(36) NULL,
    subtask_status_id INT,
    created_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    finished_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    params TEXT,
    result TEXT NULL,
    FOREIGN KEY (task_uid) REFERENCES task(task_uid),
    FOREIGN KEY (subtask_type_id) REFERENCES subtask_type(subtask_type_id),
    FOREIGN KEY (subtask_status_id) REFERENCES subtask_status(subtask_status_id),
    FOREIGN KEY (executor_uid) REFERENCES node(node_uid)
);

INSERT INTO node_status(node_status_id, name) VALUES
    (1, 'active'),
    (2, 'inactive');

INSERT INTO node_role(node_role_id, name) VALUES
    (1, 'executor'),
    (2, 'creator'),
    (3, 'registry');

INSERT INTO task_type(task_type_id, name) VALUES
    (1, 'grid_search');

INSERT INTO task_status(task_status_id, name) VALUES
    (1, 'creating'),
    (2, 'executors_searching'),
    (3, 'resources_publishing'),
    (4, 'subtasks_sending'),
    (5, 'subtasks_polling'),
    (6, 'result_processing'),
    (7, 'success'),
    (8, 'error');

INSERT INTO subtask_type(subtask_type_id, name) VALUES
    (1, 'partial_grid_search');

INSERT INTO subtask_status(subtask_status_id, name) VALUES
    (1, 'waiting_executor_assignment'),
    (2, 'creating'),
    (3, 'resources_downloading'),
    (4, 'running'),
    (5, 'success'),
    (6, 'error'),
    (7, 'timeout');
