CREATE DATABASE IF NOT EXISTS `Account`;
CREATE TABLE IF NOT EXISTS `Account`.`user` (
    `id` int NOT NULL AUTO_INCREMENT,
    `name` varchar(32) NOT NULL ,
    `password` varchar(128)  NOT NULL,
    PRIMARY KEY(`id`)
);