CREATE TABLE image_status (
    image_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE image (
    image_id VARCHAR(12) PRIMARY KEY,
    image_status_id INT
);

CREATE TABLE subtask_status (
    subtask_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE subtask (
    subtask_uid VARCHAR(36) PRIMARY KEY, -- uuid
    image_id VARCHAR(12), -- SHA-256
    container_id VARCHAR(12), -- SHA-256
    subtask_status_id INT,
    FOREIGN KEY (image_id) REFERENCES image(image_id),
    FOREIGN KEY (subtask_status_id) REFERENCES subtask_status(subtask_status_id)
);

INSERT INTO image_status(image_status_id, name) VALUES
    (1, 'creating'),
    (2, 'building'),
    (3, 'building_error'),
    (4, 'pushing'),
    (5, 'pushing_error'),
    (6, 'pushed'),
    (7, 'pulling'),
    (8, 'pulling_error'),
    (9, 'pulled'),
    (10, 'archived');

INSERT INTO subtask_status(subtask_status_id, name) VALUES
    (1, 'creating'),
    (2, 'processing'),
    (3, 'success'),
    (4, 'error'),
    (5, 'timeout'),
    (6, 'cancelled');
