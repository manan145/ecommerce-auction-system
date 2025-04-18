// Inject shared navbar + footer on every admin page
const nav = `
  <nav class="navbar">
    <div class="logo">eAuction Admin</div>
    <ul class="nav-links">
      <li><a href="../index.html">Home</a></li>
      <li><a href="index.html">Dashboard</a></li>
      <li><a href="list_reps.html">Customer Reps</a></li>
      <li><a href="category_mgmt.html">Categories</a></li>
      <li><a href="sales_reports.html">Sales Reports</a></li>
    </ul>
  </nav>`;
const footer = `<footer class="footer">© ${new Date().getFullYear()} eAuction Team</footer>`;
document.body.insertAdjacentHTML("afterbegin", nav);
document.body.insertAdjacentHTML("beforeend", footer);
