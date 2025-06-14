let editing = false;
let editingId = null;
let editingCourse = null;

// Load students from backend
function fetchStudents() {
  fetch("http://127.0.0.1:8000/view/")
    .then((res) => res.json())
    .then((data) => renderTable(data))
    .catch((err) => console.error("Error fetching:", err));
}

// Render table grouped by course
function renderTable(data) {
  const table = document.querySelector("#students tbody");
  table.innerHTML = "";

  // Group by course
  const grouped = {};
  data.forEach(student => {
    if (!grouped[student.course]) {
      grouped[student.course] = [];
    }
    grouped[student.course].push(student);
  });

  for (const course in grouped) {
    // Add a header row for the course
    const courseRow = document.createElement("tr");
    const courseCell = document.createElement("td");
    courseCell.colSpan = 8;
    courseCell.className = "table-info fw-bold text-center";
    courseCell.textContent = course;
    courseRow.appendChild(courseCell);
    table.appendChild(courseRow);

    // Now add students for this course
    grouped[course].forEach(student => {
      const row = document.createElement("tr");

      const rollTd = document.createElement("td");
      rollTd.textContent = student.roll_number;

      const nameTd = document.createElement("td");
      nameTd.textContent = student.name;

      const ageTd = document.createElement("td");
      ageTd.textContent = student.age;

      const genderTd = document.createElement("td");
      genderTd.textContent = student.gender;

      const marksTd = document.createElement("td");
      marksTd.innerHTML = Object.entries(student.mark)
        .map(([sub, mark]) => `${sub}: ${mark}`)
        .join("<br>");

      const avgTd = document.createElement("td");
      avgTd.textContent = student.avg;

      const gradeTd = document.createElement("td");
      gradeTd.textContent = student.grade;

      const actionTd = document.createElement("td");

      const editBtn = document.createElement("button");
      editBtn.className = "btn btn-sm btn-warning";
      editBtn.innerHTML = "✏️";
      editBtn.onclick = () => loadEdit(student);

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "btn btn-sm btn-danger";
      deleteBtn.innerHTML = "🗑️";
      deleteBtn.onclick = () => deleteStudent(student.roll_number, course);

      actionTd.appendChild(editBtn);
      actionTd.appendChild(deleteBtn);

      // Append all columns to the row
      row.appendChild(rollTd);
      row.appendChild(nameTd);
      row.appendChild(ageTd);
      row.appendChild(genderTd);
      row.appendChild(marksTd);
      row.appendChild(avgTd);
      row.appendChild(gradeTd);
      row.appendChild(actionTd);

      // Append row to the table
      table.appendChild(row);
    });
  }
}

// Submit form (add or update)
function submitForm() {
  const name = document.getElementById("name").value.trim();
  const age = parseInt(document.getElementById("age").value.trim());
  const gender = document.getElementById("gender").value.trim();
  const course = document.getElementById("course").value.trim();

  const sub1 = document.getElementById("sub1").value.trim();
  const mark1 = parseInt(document.getElementById("mark1").value.trim());
  const sub2 = document.getElementById("sub2").value.trim();
  const mark2 = parseInt(document.getElementById("mark2").value.trim());

  const marks = {};
  if (sub1 && !isNaN(mark1)) marks[sub1] = mark1;
  if (sub2 && !isNaN(mark2)) marks[sub2] = mark2;

  const student = { name, age, gender, course, mark: marks };

  if (editing) {
    fetch(`http://127.0.0.1:8000/update/?course=${editingCourse}&student_id=${editingId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(student),
    })
      .then((res) => res.json())
      .then(() => {
        resetForm();
        fetchStudents();
      });
  } else {
    fetch("http://127.0.0.1:8000/insert/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(student),
    })
      .then((res) => res.json())
      .then(() => {
        resetForm();
        fetchStudents();
      });
  }
}

// Load data into form for editing
function loadEdit(student) {
  editing = true;
  editingId = student.id;
  editingCourse = student.course;

  document.getElementById("name").value = student.name;
  document.getElementById("age").value = student.age;
  document.getElementById("gender").value = student.gender;
  document.getElementById("course").value = student.course;

  const subs = Object.entries(student.mark);
  document.getElementById("sub1").value = subs[0]?.[0] || "";
  document.getElementById("mark1").value = subs[0]?.[1] || "";
  document.getElementById("sub2").value = subs[1]?.[0] || "";
  document.getElementById("mark2").value = subs[1]?.[1] || "";

  document.getElementById("submitBtn").innerText = "Update Student";
}

// Delete student
function deleteStudent(rollNumber, course) {
  if (!confirm("Are you sure to delete this student?")) return;

  fetch(`http://127.0.0.1:8000/delete/?course=${course}&roll_number=${rollNumber}`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then(() => fetchStudents());
}

// Reset form
function resetForm() {
  editing = false;
  editingId = null;
  editingCourse = null;

  document.getElementById("student-form").reset();
  document.getElementById("submitBtn").innerText = "Add Student";
}

// Filter students
function applyFilter() {
  const course = document.getElementById("filterCourse").value.trim();
  const gender = document.getElementById("filterGender").value.trim();

  let url = `http://127.0.0.1:8000/students/filter?`;

  if (course) url += `course=${course}&`;
  if (gender) url += `gender=${gender}&`;

  fetch(url)
    .then((res) => res.json())
    .then((data) => renderTable(data));
}

// Load students on page load
window.onload = fetchStudents;
