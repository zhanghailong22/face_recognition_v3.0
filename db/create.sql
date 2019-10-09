CREATE DATABASE face_images;
use face_images;

CREATE TABLE image_data(
    name char(10) NOT NULL,
    image mediumblob,
    PRIMARY KEY (name)
    )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
