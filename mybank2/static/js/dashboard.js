// // Show/Hide sections
// function showSection(id) {
//   document.querySelectorAll(".content-section").forEach((s) => {
//     s.style.display = "none"; // hide all
//   });
//   document.getElementById(id).style.display = "block"; // show selected
// }

// // Populate and show update form
// function editCustomer(accno) {
//   fetch(`/admin/getCustomer/${accno}`)
//     .then((res) => res.json())
//     .then((data) => {
//       // populate hidden update form
//       document.getElementById("updateAccno").value = data.accno;
//       document.getElementById("updateName").value = data.name;
//       document.getElementById("updateMobile").value = data.mobile;
//       document.getElementById("updateEmail").value = data.email;
//       document.getElementById("updateBalance").value = data.balance;

//       // hide view table & show update form
//       showSection("updateCustomerForm");
//     })
//     .catch((err) => alert("Error fetching customer details"));
// }

// // Delete customer (keeps your existing alert logic)
// function deleteCustomer(accno) {
//   if (confirm("Are you sure you want to delete this customer?")) {
//     window.location.href = `/admin/deleteCustomer/${accno}`;
//   }
// }
