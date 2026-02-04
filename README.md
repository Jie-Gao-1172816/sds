#  Report 


## Authorship Statement

I used an AI assistant during this assignment to support my learning and development. I did not use it to submit code that I did not understand. I used it mainly for:

- **Debugging and error fixing:** I asked for help when routes did not insert data correctly (for example, missing `commit()`), when templates did not show expected values, and when SQL joins returned unexpected results.
- **SQL query design:** I asked for simpler SQL queries. This helped me review and use `JOIN`, `LEFT JOIN`, `GROUP BY`, and how to prevent duplicate enrolments.
- **Validation ideas:** I asked for validation rules based on the lecturer’s guidance (name rules, basic email checks, phone digits, and date of birth range), then implemented them in my own validation function.
- **User experience improvements:** I asked for ideas on flash messages, empty search handling, table hover effects, and button styling, and then applied them consistently across the app.

Tools used:
- ChatGPT (AI assistant) for explanations, debugging, and code suggestions.


## Design Decisions 

### 1. Overall structure and main navigation

I designed the app around the main top navigation shown in the header:

- **Home**
- **Teachers**
  - Teacher List
  - Teacher Report
- **Students**
  - Student List
  - Add Student
- **Classes**

I used this structure because it matches the main tasks of the system and keeps the site easy to navigate. Users can quickly choose the correct area (Teachers, Students, or Classes) without scrolling or guessing.

I created a **Teachers** dropdown with **Teacher List** and **Teacher Report**. I created a **Students** dropdown with **Student List** and **Add Student**. I placed **Add Student** inside the Students menu because adding a student is a common task and should be easy to find. I also wanted the Teachers and Students menus to look balanced and consistent.

### 2. Theme and colour choices (black / white / grey)

I used a simple black, white, and grey colour palette across the whole site. I chose these colours because they match the dance school style and also make the pages look clean and professional. The neutral colours work well with the homepage dance image, and they keep tables and forms easy to read. I also kept the header and footer consistent on every page so the interface feels stable and familiar.

### 3. Student List search feedback

Student search allows an empty input. If the user submits an empty search, a flash message shows **“No search term entered. Showing all students.”** This avoids a confusing blank page.  
If no students match the search term, a flash message shows **“No students matched your search.”** This helps the user understand the result and try a better keyword.

### 4. Flash messages for key actions

I used flash messages for **Add Student**, **Edit Student**, and **Enrol Student** section. This gives users clear feedback. They can see if an action was successful or if something needs to be fixed.


### 5. Using GET and POST methods (reasons and where I used them)

I used **GET** when the user needs to **view a page or open a form**. GET is suitable because it does not change database data and it allows pages to be opened using a URL with query parameters (for example, `?student_id=...`).  
Examples in my app:
- **Student List** and search results (view data)
- **Edit Student (GET)** to load the existing student details into the form
- **Add Student (GET)** to show an empty form
- **Enrol Student (GET)** to show eligible classes for the selected student
- **Teacher List / Teacher Report (GET)** and **Class List (GET)** to display information

I used **POST** when the user submits a form and the app needs to **create or update data**. POST is suitable because it changes the database and it prevents sensitive form data from being placed in the URL.  
Examples in my app:
- **Add Student (POST)** to insert a new student record
- **Edit Student (POST)** to update an existing student record
- **Enrol Student (POST)** to insert a new enrolment into `studentclasses` (with a duplicate check)


### 6. Class list grouping to avoid repeated class names

One class can have many students. If I display the raw join result, the same class name repeats multiple times. This is not neat and not user friendly.  
I grouped students under the same class and only displayed the class details once. This will make the class list more readable.


### 7. Class list readability (consistent grouping)

For better readability, I kept each class group visually consistent. This makes the table easier to scan and reduces mistakes when reading student lists.


### 8. Student Class Summary and handling grade discrepancies

The Student Class Summary page is designed to shows the student’s enrolled classes and student current grade inforamtion.

During testing, I noticed a discrepancy between `studentgrades` (the student’s recorded grade) and the grade level of the class the student is enrolled in. For example, **Lucas Harris** has a mismatch between the recorded grade and the class grade. I do not know if this is test data or a mistake. To handle this clearly, I display the student’s current grades on the summary page. If a user finds a mismatch, the best solution is to edit the student grade first to match the current class grade and then enrol the correct class grade again. User can find decription on enrol page, if the class grade which can be enroled is not match current class grade.

### 11. Button priority based on user goals

When a page has several actions, I used different button styles to guide users. For example, **Back to Student List** is less important, so it uses a lighter style. **Enrol in a Class** is a main task, so it is more visible.


### 12. Multiple entry points for key actions

I added links to **Enrol Student** and **Edit Student** from both **Student List** and **Student Class Summary**. This reduces clicks and makes important actions easier to find.

### 13. Date inputs with HTML date picker

I used `today = date.today().isoformat()` and HTML date inputs for **Date of Birth** and **Enrollment Date**. This makes date entry easier and reduces formatting errors. It also supports a realistic age assumption by limiting the selectable date range.

### 14. Preserving user input after validation errors

If a user submits a form with errors on edit or add stduent section, I re-render the form instead of redirecting. This keeps the correct values in the form so the user does not need to re-enter everything.

### 15. Enrolment requires student qualification

Enrolment options are only shown when the student is qualified. If the student has no grade data, the page shows a clear message suggesting the user sets grades first. This matches the assignment requirement that only qualified classes should be shown.



## Image Sources (APA 7)

Moryak, N. (n.d.). *Dancers sitting on white floor* [Photograph]. Pexels. https://www.pexels.com/photo/dancers-sitting-on-white-floor-7667562/





## Database Question

To support parents/caregivers, I would add a new **Parents (Caregivers)** table to store parent information. This table could include fields such as `parent_id` (primary key), `first_name`, `last_name`, `email`, `phone`, and possibly `address` and `is_active`. I would also add a **link table** (for example, `parent_students`) to connect parents and students. The link table should include `parent_student_id` (primary key), `parent_id` (foreign key), `student_id` (foreign key), and a field like `relationship` (e.g., mother, father, guardian) or `is_primary_contact` (yes/no). This structure supports the real situation that one parent can have multiple children, and one student can have more than one caregiver. It also reduces duplicated data, because the same parent details do not need to be stored in every student record. If a parent changes their phone or email, it can be updated once and will apply to all linked students. With these changes, the app could add parent features such as viewing all children’s enrolled classes, receiving class notifications, and updating contact details in one place.
