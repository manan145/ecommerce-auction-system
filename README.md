# BuyMe Auction System

A full-featured online auction platform with role-based access control, dynamic product management, and real-time bidding.

## Team Members
- **Manan Jagani** (NetID: mj868)  
- **Krish Shah** (NetID: ks1984)  
- **Vineeth Ajith John** (NetID: fv122)  
- **Sathvick Sudarsan** (NetID: ss4800)

---

## General Features

- **User Registration & Login**  
  Secure signup with email validation, password hashing, and JWT-based authentication. Registration is available only for buyers and sellers. Customer reps can only be added by the admin.

- **Role-Based Access Control**  
  Four separate dashboards and API endpoints for buyers, sellers, customer reps, and admins.

- **Notifications & Alerts**  
  In-app alerts for bids, payment notifications, and matching custom alerts.

- **Support & Password Recovery**  
  Access FAQs and submit support tickets.

- **Background Scheduler**  
  APScheduler task closes expired auctions and finalizes transactions periodically.

---

## Buyer Dashboard

The Buyer dashboard enables users to browse auctions, place manual and auto bids, manage notifications, and contact support.

### Features

- **Landing Page**  
  Welcome screen with an overview of available tools.

- **Auction Browsing**  
  - Browse active auctions with filters for category, subcategory, price, and all attributes (loaded dynamically via AJAX).  
  - Filters adjust based on selected subcategory.  
  - View item details and bid history in modal dialogs.

- **Bidding**  
  - Supports real-time bidding with both manual and auto-bid options. Automatically simulates bidding wars when multiple users enable auto-bidding on the same auction.

- **My Bids**  
  Track current bids for a specific user, display winning/losing status, and view detailed bid timelines including older multi-bid histories.

- **Create Alerts**  
  Define criteria (category, brand, model, condition) for alerts when new items become available.

- **View Alerts**  
  List all created alerts with options to delete them.

- **Similar Items**  
  View closed auctions from the past month similar to a chosen listing using fuzzy attribute matching.

- **FAQs**  
  Accordion-style Q&A with keyword search using fuzzy matching.

- **Contact Support**  
  Submit and track support tickets. View conversation threads and status.

- **Bid History**  
  Comprehensive history of all bids placed on a particular auction.

---

## Customer Representative Dashboard

The Customer Rep module supports the following functionalities:

### Features

- **Dashboard Overview**  
  Welcome landing page with sidebar navigation.

- **Profile Management**  
  View rep profile (Rep ID, Department, Shift).  
  Edit department and shift via form.

- **User Management**  
  - Search users by email.  
  - Update buyer/seller usernames and emails.  
  - Delete user accounts.

- **Password Reset**  
  Generate temporary passwords by email lookup and notify users.  
  These users can log in again using the temporary password.

- **Auction & Bid Oversight**  
  - View auctions with metadata (item, brand, category).  
  - Inspect auction details and item specs in modals.  
  - Delete auctions or individual bids.

- **Customer Queries**  
  - List unresolved queries.  
  - Respond inline via text input.  
  - Mark queries as resolved.

---

## Seller Dashboard

The Seller dashboard enables users to manage items, launch auctions, and track sales in a unified interface.

### Features

- **Landing Page**  
  Welcome landing page with sidebar navigation.

- **Item Management**  
  - **Create Item**: Enter brand, model, title, description, condition, category, subcategory, and custom attributes.  
  - **View & Edit Items**: List all items with sold/unsold status badges; edit or delete items.

- **Auction Management**  
  - **Create Auction**: Select an item and configure start price, secret reserve, minimum increment, and start/end times.  
  - **Extend Auction**: Add extra time to active auctions before they close.  
  - **Withdraw Auction**: Cancel auctions prior to closure.  
  - **Bid Overview**: Real-time list of bids per auction, view highest bid, and detailed bid history in a modal.

- **Support Access**  
  Direct link to FAQs and support ticket creation.

---

## Admin Dashboard

The Admin dashboard empowers administrators to configure the platform, manage reps, oversee users, and monitor system-wide performance.

### Features

- **Landing Page**  
  Welcome landing page with sidebar navigation.

- **Representative Administration**  
  - **Create Representative**: Add reps with username, email, department, and shift.  
  - **Manage Representatives**: Search, view, update, or delete reps; change rep status.

- **Category & Taxonomy Management**  
  Admins can dynamically manage product types without modifying code.  
  - **Manage Categories**: Add, edit, or delete product categories.  
  - **Manage Subcategories**: Choose a category to add/edit/remove subcategories.  
  - **Manage Attributes**: Assign comma-separated attributes to subcategories; dropdowns refresh dynamically via AJAX.

- **Sales Reports & Analytics**  
  - **Scorecards**: Real-time display of total revenue and all earning types.  
  - **Interactive Charts**: Chart.js-powered bar and pie charts for sales trends and category breakdowns.  
  - **CSV Export**: Generate and download sales reports.
