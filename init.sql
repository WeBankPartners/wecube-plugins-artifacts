SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8;

--
-- Table structure initialize
--

CREATE TABLE diff_conf_template (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(16) NOT NULL COMMENT '类型：app/db/xx',
    code VARCHAR(36) NOT NULL COMMENT '编码',
    value TEXT NULL COMMENT '文本值',
    description VARCHAR(128) DEFAULT '' COMMENT '描述',
    create_user VARCHAR(36) DEFAULT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_user VARCHAR(36) DEFAULT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0 COMMENT '软删除:0,1',
    INDEX (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE diff_conf_template_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    permission VARCHAR(16) NOT NULL COMMENT '权限：MGMT/USE/xx',
    role VARCHAR(64) NOT NULL COMMENT '角色',
    diff_conf_template_id BIGINT,
    CONSTRAINT fk_diff_conf_template
        FOREIGN KEY (diff_conf_template_id)
        REFERENCES diff_conf_template (id)
        ON DELETE CASCADE,
    INDEX (diff_conf_template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


#@v1.2.1.3-begin@;
alter table diff_conf_template
    modify type varchar(16) null comment '类型：应用-app,数据库-db';
#@v1.2.1.3-end@;


#@v1.2.1.5-begin@;
alter table diff_conf_template add constraint uk_is_deleted_code unique (code, is_deleted);
#@v1.2.1.5-end@;


#@v1.2.1.10-begin@;
alter table diff_conf_template drop key uk_is_deleted_code;
alter table diff_conf_template drop column is_deleted;
alter table diff_conf_template add unique (code);
#@v1.2.1.10-end@;


-- alter table diff_conf_template modify column create_time datetime default current_timestamp;
-- alter table diff_conf_template modify column update_time datetime default current_timestamp on update current_timestamp;

#@v1.5.3.7-begin@;
CREATE TABLE private_variable_template (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(36) NOT NULL COMMENT '私有变量名称',
    diff_conf_template_id BIGINT NOT NULL,
    description VARCHAR(128) DEFAULT '' COMMENT '描述',
    create_user VARCHAR(36) DEFAULT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_user VARCHAR(36) DEFAULT NULL,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#@v1.5.3.7-end@;