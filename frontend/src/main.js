document.addEventListener('DOMContentLoaded', () => {
  const nav = document.createElement('nav');
  nav.innerHTML = `
    <ul>
      <li><a href="./admin/create_rep.html">Create Rep</a></li>
      <li><a href="./admin/list_reps.html">List Reps</a></li>
      <li><a href="./admin/category_mgmt.html">Category Management</a></li>
      <li><a href="./admin/sales_reports.html">Sales Reports</a></li>
    </ul>
  `;
  document.body.prepend(nav);
});