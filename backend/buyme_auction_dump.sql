-- MySQL dump 10.13  Distrib 5.7.24, for osx11.1 (x86_64)
--
-- Host: localhost    Database: buyme_auction
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Admin`
--

DROP TABLE IF EXISTS `Admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Admin` (
  `AdminID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `AccessLevel` enum('SuperAdmin','Manager','ReadOnly') NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `LastLogin` datetime DEFAULT NULL,
  PRIMARY KEY (`AdminID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `admin_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Admin`
--

LOCK TABLES `Admin` WRITE;
/*!40000 ALTER TABLE `Admin` DISABLE KEYS */;
INSERT INTO `Admin` VALUES (1,1,'SuperAdmin','2025-04-13 18:51:10','2025-04-13 15:44:32');
/*!40000 ALTER TABLE `Admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Alert`
--

DROP TABLE IF EXISTS `Alert`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Alert` (
  `AlertID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `Category` varchar(50) NOT NULL
  `Subcategory` varchar(50) NOT NULL,
  `SearchCriteria` json NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`AlertID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `alert_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Alert`
--

LOCK TABLES `Alert` WRITE;
/*!40000 ALTER TABLE `Alert` DISABLE KEYS */;
/*!40000 ALTER TABLE `Alert` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Attribute`
--

DROP TABLE IF EXISTS `Attribute`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Attribute` (
  `AttributeID` int NOT NULL AUTO_INCREMENT,
  `SubcategoryID` int NOT NULL,
  `Name` varchar(50) NOT NULL,
  PRIMARY KEY (`AttributeID`),
  KEY `SubcategoryID` (`SubcategoryID`),
  CONSTRAINT `attribute_ibfk_1` FOREIGN KEY (`SubcategoryID`) REFERENCES `Subcategory` (`SubcategoryID`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Attribute`
--

LOCK TABLES `Attribute` WRITE;
/*!40000 ALTER TABLE `Attribute` DISABLE KEYS */;
INSERT INTO `Attribute` VALUES (1,1,'Processor'),(2,1,'RAM'),(3,1,'Storage'),(4,1,'Screen Size'),(5,1,'Graphics Card'),(6,1,'Operating System'),(7,1,'Battery Life'),(8,1,'Weight'),(9,1,'Warranty'),(10,2,'Storage'),(11,2,'RAM'),(12,2,'Color'),(13,2,'Operating System'),(14,2,'Screen Size'),(15,2,'Camera'),(16,2,'Battery Capacity'),(17,2,'Network Support'),(18,2,'Warranty'),(19,4,'Type'),(20,4,'Wireless'),(21,4,'Noise Cancellation'),(22,4,'Battery Life'),(23,4,'Charging Port'),(24,4,'Color'),(25,4,'Mic Included'),(26,4,'Waterproof Rating'),(27,4,'Warranty'),(28,3,'Screen Size'),(29,3,'Resolution'),(30,3,'Panel Type'),(31,3,'Refresh Rate'),(32,3,'Ports'),(33,3,'Response Time'),(34,3,'Aspect Ratio'),(35,3,'Adjustable Stand'),(36,3,'VESA Mount Support'),(37,3,'Warranty');
/*!40000 ALTER TABLE `Attribute` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Auction`
--

DROP TABLE IF EXISTS `Auction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auction` (
  `AuctionID` int NOT NULL AUTO_INCREMENT,
  `ItemID` int NOT NULL,
  `StartPrice` decimal(10,2) NOT NULL,
  `MinIncrement` decimal(10,2) NOT NULL,
  `SecretMinPrice` decimal(10,2) NOT NULL,
  `StartTime` datetime NOT NULL,
  `EndTime` datetime NOT NULL,
  `IsClosed` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`AuctionID`),
  KEY `ItemID` (`ItemID`),
  CONSTRAINT `auction_ibfk_1` FOREIGN KEY (`ItemID`) REFERENCES `Item` (`ItemID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Auction`
--

LOCK TABLES `Auction` WRITE;
/*!40000 ALTER TABLE `Auction` DISABLE KEYS */;
/*!40000 ALTER TABLE `Auction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Bid`
--

DROP TABLE IF EXISTS `Bid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Bid` (
  `BidID` int NOT NULL AUTO_INCREMENT,
  `AuctionID` int NOT NULL,
  `BidderID` int NOT NULL,
  `Amount` decimal(10,2) NOT NULL,
  `BidTime` datetime DEFAULT CURRENT_TIMESTAMP,
  `MaxAutoBid` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`BidID`),
  KEY `AuctionID` (`AuctionID`),
  KEY `BidderID` (`BidderID`),
  CONSTRAINT `bid_ibfk_1` FOREIGN KEY (`AuctionID`) REFERENCES `Auction` (`AuctionID`),
  CONSTRAINT `bid_ibfk_2` FOREIGN KEY (`BidderID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Bid`
--

LOCK TABLES `Bid` WRITE;
/*!40000 ALTER TABLE `Bid` DISABLE KEYS */;
/*!40000 ALTER TABLE `Bid` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Category`
--

DROP TABLE IF EXISTS `Category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Category` (
  `CategoryID` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(50) NOT NULL,
  PRIMARY KEY (`CategoryID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Category`
--

LOCK TABLES `Category` WRITE;
/*!40000 ALTER TABLE `Category` DISABLE KEYS */;
INSERT INTO `Category` VALUES (1,'Electronics');
/*!40000 ALTER TABLE `Category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CustomerRep`
--

DROP TABLE IF EXISTS `CustomerRep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CustomerRep` (
  `RepID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `AssignedBy` int DEFAULT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `Department` varchar(50) DEFAULT NULL,
  `Shift` varchar(20) DEFAULT NULL,
  `Status` enum('active','inactive') DEFAULT 'active',
  PRIMARY KEY (`RepID`),
  KEY `UserID` (`UserID`),
  KEY `AssignedBy` (`AssignedBy`),
  CONSTRAINT `customerrep_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `customerrep_ibfk_2` FOREIGN KEY (`AssignedBy`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CustomerRep`
--

LOCK TABLES `CustomerRep` WRITE;
/*!40000 ALTER TABLE `CustomerRep` DISABLE KEYS */;
/*!40000 ALTER TABLE `CustomerRep` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Feedback`
--

DROP TABLE IF EXISTS `Feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Feedback` (
  `FeedbackID` int NOT NULL AUTO_INCREMENT,
  `FromUserID` int NOT NULL,
  `ToUserID` int NOT NULL,
  `Rating` int NOT NULL,
  `Comment` text,
  `Date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`FeedbackID`),
  KEY `FromUserID` (`FromUserID`),
  KEY `ToUserID` (`ToUserID`),
  CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`FromUserID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `feedback_ibfk_2` FOREIGN KEY (`ToUserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Feedback`
--

LOCK TABLES `Feedback` WRITE;
/*!40000 ALTER TABLE `Feedback` DISABLE KEYS */;
/*!40000 ALTER TABLE `Feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Item`
--

DROP TABLE IF EXISTS `Item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Item` (
  `ItemID` int NOT NULL AUTO_INCREMENT,
  `Title` varchar(100) NOT NULL,
  `Brand` varchar(50) NOT NULL,
  `Model` varchar(100) NOT NULL,
  `Condition` enum('New','Open Box','Refurbished','Used') DEFAULT NULL,
  `Description` text,
  `OwnerID` int NOT NULL,
  `CategoryID` int NOT NULL,
  `SubcategoryID` int NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `Status` enum('active','withdrawn','sold') DEFAULT 'active',
  PRIMARY KEY (`ItemID`),
  KEY `OwnerID` (`OwnerID`),
  KEY `CategoryID` (`CategoryID`),
  KEY `SubcategoryID` (`SubcategoryID`),
  CONSTRAINT `item_ibfk_1` FOREIGN KEY (`OwnerID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `item_ibfk_2` FOREIGN KEY (`CategoryID`) REFERENCES `Category` (`CategoryID`),
  CONSTRAINT `item_ibfk_3` FOREIGN KEY (`SubcategoryID`) REFERENCES `Subcategory` (`SubcategoryID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Item`
--

LOCK TABLES `Item` WRITE;
/*!40000 ALTER TABLE `Item` DISABLE KEYS */;
/*!40000 ALTER TABLE `Item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItemAttributeValue`
--

DROP TABLE IF EXISTS `ItemAttributeValue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ItemAttributeValue` (
  `ItemID` int NOT NULL,
  `AttributeID` int NOT NULL,
  `Value` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ItemID`,`AttributeID`),
  KEY `AttributeID` (`AttributeID`),
  CONSTRAINT `itemattributevalue_ibfk_1` FOREIGN KEY (`ItemID`) REFERENCES `Item` (`ItemID`),
  CONSTRAINT `itemattributevalue_ibfk_2` FOREIGN KEY (`AttributeID`) REFERENCES `Attribute` (`AttributeID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItemAttributeValue`
--

LOCK TABLES `ItemAttributeValue` WRITE;
/*!40000 ALTER TABLE `ItemAttributeValue` DISABLE KEYS */;
/*!40000 ALTER TABLE `ItemAttributeValue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Message`
--

DROP TABLE IF EXISTS `Message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Message` (
  `MessageID` int NOT NULL AUTO_INCREMENT,
  `SenderID` int NOT NULL,
  `ReceiverID` int NOT NULL,
  `Content` text NOT NULL,
  `Timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`MessageID`),
  KEY `SenderID` (`SenderID`),
  KEY `ReceiverID` (`ReceiverID`),
  CONSTRAINT `message_ibfk_1` FOREIGN KEY (`SenderID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `message_ibfk_2` FOREIGN KEY (`ReceiverID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Message`
--

LOCK TABLES `Message` WRITE;
/*!40000 ALTER TABLE `Message` DISABLE KEYS */;
/*!40000 ALTER TABLE `Message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Notification`
--

DROP TABLE IF EXISTS `Notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Notification` (
  `NotificationID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `Message` varchar(255) NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `Status` enum('unread','read') DEFAULT 'unread',
  PRIMARY KEY (`NotificationID`),
  KEY `UserID` (`UserID`),
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Notification`
--

LOCK TABLES `Notification` WRITE;
/*!40000 ALTER TABLE `Notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `Notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Subcategory`
--

DROP TABLE IF EXISTS `Subcategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subcategory` (
  `SubcategoryID` int NOT NULL AUTO_INCREMENT,
  `CategoryID` int NOT NULL,
  `Name` varchar(50) NOT NULL,
  PRIMARY KEY (`SubcategoryID`),
  KEY `CategoryID` (`CategoryID`),
  CONSTRAINT `subcategory_ibfk_1` FOREIGN KEY (`CategoryID`) REFERENCES `Category` (`CategoryID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Subcategory`
--

LOCK TABLES `Subcategory` WRITE;
/*!40000 ALTER TABLE `Subcategory` DISABLE KEYS */;
INSERT INTO `Subcategory` VALUES (1,1,'Laptops'),(2,1,'Smartphones'),(3,1,'Monitors'),(4,1,'Headphones');
/*!40000 ALTER TABLE `Subcategory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Transaction`
--

DROP TABLE IF EXISTS `Transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Transaction` (
  `TransactionID` int NOT NULL AUTO_INCREMENT,
  `AuctionID` int NOT NULL,
  `BuyerID` int NOT NULL,
  `Price` decimal(10,2) NOT NULL,
  `TransactionDate` datetime DEFAULT CURRENT_TIMESTAMP,
  `Status` enum('completed','pending','cancelled') DEFAULT 'completed',
  PRIMARY KEY (`TransactionID`),
  KEY `AuctionID` (`AuctionID`),
  KEY `BuyerID` (`BuyerID`),
  CONSTRAINT `transaction_ibfk_1` FOREIGN KEY (`AuctionID`) REFERENCES `Auction` (`AuctionID`),
  CONSTRAINT `transaction_ibfk_2` FOREIGN KEY (`BuyerID`) REFERENCES `User` (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Transaction`
--

LOCK TABLES `Transaction` WRITE;
/*!40000 ALTER TABLE `Transaction` DISABLE KEYS */;
/*!40000 ALTER TABLE `Transaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `User` (
  `UserID` int NOT NULL AUTO_INCREMENT,
  `Username` varchar(50) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `PasswordHash` varchar(255) NOT NULL,
  `Role` enum('buyer','seller','customer_rep','admin') NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`UserID`),
  UNIQUE KEY `Email` (`Email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `User`
--

LOCK TABLES `User` WRITE;
/*!40000 ALTER TABLE `User` DISABLE KEYS */;
INSERT INTO `User` VALUES (1,'admin1','admin1@example.com','scrypt:32768:8:1$SA3DxaTFho6Mott5$28b3bdb8ac87ac5b3de130f4a69167e8fdcf05b109dc894fd251d1098757103c28d9e54aa77aaff89d8b78b0243202b451788d1c959be1cca20f38595a36dccc','admin','2025-04-13 18:51:10');
/*!40000 ALTER TABLE `User` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Watchlist`
--

DROP TABLE IF EXISTS `Watchlist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Watchlist` (
  `WatchlistID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `AuctionID` int NOT NULL,
  `CreatedAt` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`WatchlistID`),
  KEY `UserID` (`UserID`),
  KEY `AuctionID` (`AuctionID`),
  CONSTRAINT `watchlist_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `User` (`UserID`),
  CONSTRAINT `watchlist_ibfk_2` FOREIGN KEY (`AuctionID`) REFERENCES `Auction` (`AuctionID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Watchlist`
--

LOCK TABLES `Watchlist` WRITE;
/*!40000 ALTER TABLE `Watchlist` DISABLE KEYS */;
/*!40000 ALTER TABLE `Watchlist` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-13 11:59:08
