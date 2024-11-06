#@v1.1.12.1-begin@;
CREATE TABLE diff_conf_template (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(16) NOT NULL COMMENT '类型：应用-app,数据库-db',
    code VARCHAR(36) NOT NULL COMMENT '编码',
    value TEXT NULL COMMENT '文本值',
    description VARCHAR(128) DEFAULT '' COMMENT '描述',
    create_user VARCHAR(36) DEFAULT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_user VARCHAR(36) DEFAULT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0 COMMENT '软删除:0,1',
    INDEX (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE diff_conf_template_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    permission VARCHAR(16) NOT NULL COMMENT '权限：MGMT,USE',
    role VARCHAR(64) NOT NULL COMMENT '角色',
    diff_conf_template_id BIGINT,
    CONSTRAINT fk_diff_conf_template
        FOREIGN KEY (diff_conf_template_id)
        REFERENCES diff_conf_template (id)
        ON DELETE CASCADE,
    INDEX (diff_conf_template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#@v1.1.12.1-end@;


