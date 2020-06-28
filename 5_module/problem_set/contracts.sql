CREATE TABLE contractors
(
    contractor_id INTEGER,
    global_vendor_name TEXT,
    PRIMARY KEY (contractor_id)
);

CREATE TABLE actions
(
    id INTEGER,
    department TEXT,
    actions INTEGER,
    dollars REAL,
    contractor_id INTEGER,
    FOREIGN KEY (contractor_id)
       REFERENCES contractors (contractor_id)
);