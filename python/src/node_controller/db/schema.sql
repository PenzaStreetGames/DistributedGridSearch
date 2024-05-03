CREATE TABLE node_status (
    node_status_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE node_role (
    node_role_id INT PRIMARY KEY,
    name VARCHAR(64)
);

CREATE TABLE nodes (
    node_uid VARCHAR(36) PRIMARY KEY, -- uuid
    ipv4_address VARCHAR(21), -- 255.255.255.255:65535
    last_ping VARCHAR(23), -- YYYY-MM-DD HH:MM:SS.SSS
    node_role_id INT,
    node_status_id INT,
    FOREIGN KEY (node_status_id) REFERENCES node_status(node_status_id),
    FOREIGN KEY (node_role_id) REFERENCES node_role(node_role_id)
);

INSERT INTO node_status(node_status_id, name) VALUES
    (1, 'active'),
    (2, 'inactive');

INSERT INTO node_role(node_role_id, name) VALUES
    (1, 'executor'),
    (2, 'creator'),
    (3, 'registry');
