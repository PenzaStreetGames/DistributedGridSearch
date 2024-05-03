CREATE TABLE dataset_status (
    dataset_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE dataset (
    dataset_uid VARCHAR(36) PRIMARY KEY, -- uuid
    magnet_link VARCHAR(256),
    destination VARCHAR(256), -- path to directory
    dataset_status_id INT
);

INSERT INTO dataset_status VALUES
    (1, 'creating'),
    (2, 'publishing'),
    (3, 'downloading'),
    (4, 'available');
