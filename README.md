# ecommerce-auction-system

## Setting Up the Database

To set up the database for the BuyMe Auction project, follow these steps:

1. **Install MySQL**:
   Ensure you have MySQL installed on your system. You can download it from [MySQL Downloads](https://dev.mysql.com/downloads/).

2. **Create the Database**:
   Open your MySQL client and run the following command to create a new database:
   ```sql
   CREATE DATABASE buyme_auction;
   ```

3. **Import the Dump File**:
   Navigate to the `backend/` directory where the `buyme_auction_dump.sql` file is located. Run the following command to import the dump file:
   ```bash
   mysql -u <your_username> -p buyme_auction < buyme_auction_dump.sql
   ```
   Replace `<your_username>` with your MySQL username. You will be prompted to enter your password.

4. **Verify the Import**:
   After the import, you can verify the tables and data by running:
   ```sql
   USE buyme_auction;
   SHOW TABLES;
   ```

Your database should now be set up and ready to use with the BuyMe Auction project.