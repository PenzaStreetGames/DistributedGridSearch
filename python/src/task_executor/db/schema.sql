CREATE TABLE subtask_status (
    subtask_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE subtask (
    subtask_uid VARCHAR(36) PRIMARY KEY, -- uuid
    creator_uid VARCHAR(36),
    dataset_uid VARCHAR(36) NULL,
    subtask_status_id INT,
    created_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    finished_at VARCHAR(23) NULL, -- YYYY-MM-DD HH:MM:SS.SSS
    FOREIGN KEY (subtask_status_id) REFERENCES subtask_status(subtask_status_id)
);

INSERT INTO subtask_status(subtask_status_id, name) VALUES
    (1, 'waiting_params'),
    (2, 'creating'),
    (3, 'processing'),
    (4, 'success'),
    (5, 'error'),
    (6, 'timeout'),
    (7, 'cancelled');
