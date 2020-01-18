DROP DATABASE thoughts;
CREATE DATABASE thoughts;
USE thoughts;
CREATE TABLE users (
	id int not null primary key auto_increment,
    firstname varchar(100),
    lastname varchar(100),
    pw varchar(255),
    email varchar(100),
    created_at timestamp default current_timestamp,
    modified_at datetime
);

CREATE TABLE thoughts (
	id int not null primary key auto_increment,
    content varchar(255),
    userid int not null,
    created_at timestamp default current_timestamp,
    modified_at datetime,
    FOREIGN KEY (userid) REFERENCES users (id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE TABLE likes (
	id int not null primary key auto_increment,
    userid int not null,
    thoughtid int not null,
    created_at timestamp default current_timestamp,
    modified_at datetime,
	FOREIGN KEY (userid) REFERENCES users (id)
		ON DELETE CASCADE,
	FOREIGN KEY (thoughtid) REFERENCES thoughts (id)
		ON DELETE CASCADE
    );
