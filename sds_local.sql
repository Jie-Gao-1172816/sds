create schema sds;   
use sds;

CREATE TABLE dancetype (
    dancetype_id INT AUTO_INCREMENT PRIMARY KEY,
    dancetype_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE grades (
    grade_id INT AUTO_INCREMENT PRIMARY KEY,
    grade_name VARCHAR(50) NOT NULL UNIQUE,
    grade_level INT
);

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    date_of_birth DATE,
    enrollment_date DATE DEFAULT (CURRENT_DATE),
    is_active BOOLEAN DEFAULT TRUE
);


CREATE TABLE teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);


CREATE TABLE teacherdancetypes (
    teacherdancetype_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    dancetype_id INT NOT NULL,
    UNIQUE KEY unique_teacher_dancetype (teacher_id, dancetype_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    FOREIGN KEY (dancetype_id) REFERENCES dancetype(dancetype_id) ON DELETE CASCADE
);


CREATE TABLE classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    dancetype_id INT NOT NULL,
    grade_id INT,
    teacher_id INT NOT NULL,
    schedule_day VARCHAR(20),
    schedule_time TIME,
    FOREIGN KEY (dancetype_id) REFERENCES dancetype(dancetype_id) ON DELETE RESTRICT,
    FOREIGN KEY (grade_id) REFERENCES grades(grade_id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE RESTRICT
);

CREATE TABLE studentclasses (
    studentclass_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    UNIQUE KEY unique_student_class (student_id, class_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE
);


CREATE TABLE studentgrades (
    studentgrade_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    grade_id INT NOT NULL,
    dancetype_id INT NOT NULL,
    UNIQUE KEY unique_student_grade_dance (student_id, grade_id, dancetype_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (grade_id) REFERENCES grades(grade_id) ON DELETE RESTRICT,
    FOREIGN KEY (dancetype_id) REFERENCES dancetype(dancetype_id) ON DELETE RESTRICT
);



INSERT INTO dancetype (dancetype_name) VALUES
('Ballet'),
('Jazz'),
('Modern'),
('Tap')
;


INSERT INTO grades (grade_name, grade_level) VALUES
('Pre-Primary', 0),
('Grade 1', 1),
('Grade 2', 2),
('Grade 3', 3),
('Grade 4', 4),
('Grade 5', 5),
('Intermediate', 6),
('Advanced', 7);

INSERT INTO teachers (first_name, last_name, email, phone) VALUES
('Sarah', 'Johnson', 'sarah.j@danceschool.com', '021 456 7890' ),
('Michael', 'Chen', 'michael.c@danceschool.com', '027 234 5678'),
('Emma', 'Rodriguez', 'emma.r@danceschool.com', '022 987 6543');


INSERT INTO teacherdancetypes (teacher_id, dancetype_id) VALUES
(1, 1),
(1, 3);

INSERT INTO teacherdancetypes (teacher_id, dancetype_id) VALUES
(2, 2),
(2, 3);

INSERT INTO teacherdancetypes (teacher_id, dancetype_id) VALUES
(3, 4),
(3, 1);


INSERT INTO students (first_name, last_name, email, phone, date_of_birth, enrollment_date) VALUES
('Emily', 'Wilson', 'emily.wilson@email.com', '021 111 2222', '2012-03-15', '2023-01-10'),
('Oliver', 'Brown', 'oliver.brown@email.com', '022 333 4444', '2013-07-22', '2023-02-15'),
('Sophia', 'Taylor', 'sophia.taylor@email.com', '027 555 6666', '2011-11-08', '2022-09-01'),
('Jack', 'Anderson', 'jack.anderson@email.com', '021 777 8888', '2014-05-30', '2024-01-20'),
('Isabella', 'Thomas', 'isabella.thomas@email.com', '022 999 0000', '2012-09-14', '2023-03-05'),
('Noah', 'Jackson', 'noah.jackson@email.com', '027 111 3333', '2013-02-28', '2023-06-12'),
('Mia', 'White', 'mia.white@email.com', '021 222 4444', '2015-08-19', '2024-02-01'),
('Lucas', 'Harris', 'lucas.harris@email.com', '022 444 5555', '2011-12-03', '2022-08-15'),
('Amelia', 'Martin', 'amelia.martin@email.com', '027 666 7777', '2014-04-25', '2023-10-08'),
('Liam', 'Thompson', 'liam.thompson@email.com', '021 888 9999', '2013-10-11', '2023-05-20');


INSERT INTO classes (class_name, dancetype_id, grade_id, teacher_id, schedule_day, schedule_time) VALUES
('Ballet Beginners', 1, 1, 1, 'Monday', '16:00:00'),
('Ballet Grade 2', 1, 3, 1, 'Tuesday', '17:00:00'),
('Jazz Intermediate', 2, 6, 2, 'Wednesday', '16:30:00'),
('Modern Dance Advanced', 3, 7, 2, 'Thursday', '18:00:00'),
('Tap Grade 1', 4, 2, 3, 'Friday', '16:00:00'),
('Ballet Pre-Primary', 1, 1, 3, 'Saturday', '10:00:00'),
('Jazz Grade 3', 2, 4, 2, 'Monday', '17:30:00'),
('Modern Dance Grade 2', 3, 3, 1, 'Wednesday', '17:00:00');


INSERT INTO studentgrades (student_id, grade_id, dancetype_id) VALUES
(1, 2, 1),
(1, 1, 2),
(2, 1, 1),
(2, 2, 4),
(3, 3, 1),
(3, 3, 3),
(3, 2, 2),
(4, 1, 1),
(5, 2, 1),
(5, 2, 2),
(6, 2, 3),
(6, 1, 4),
(7, 1, 1),
(8, 4, 1),
(8, 3, 2),
(8, 3, 3),
(9, 2, 2),
(9, 1, 1),
(10, 2, 1),
(10, 2, 4);


INSERT INTO studentclasses (student_id, class_id) VALUES
(1, 2),
(2, 1),
(2, 5),
(3, 2),
(3, 8),
(3, 7),
(4, 6),
(5, 1),
(5, 7),
(6, 8),
(7, 6),
(8, 3),
(8, 8),
(9, 1),
(10, 2),
(10, 5);
