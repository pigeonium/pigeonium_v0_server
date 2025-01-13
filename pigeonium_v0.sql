-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/

-- server: 8.0.40-0ubuntu0.22.04.1
-- PHP: 8.1.2-1ubuntu2.20

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;

CREATE TABLE `balance` (
  `address` binary(16) NOT NULL,
  `currencyId` binary(16) NOT NULL,
  `amount` bigint NOT NULL
);

CREATE TABLE `currency` (
  `currencyId` binary(16) NOT NULL,
  `name` varchar(32) NOT NULL,
  `symbol` varchar(8) NOT NULL,
  `inputData` varbinary(4096) NOT NULL,
  `issuer` binary(16) NOT NULL,
  `supply` bigint UNSIGNED NOT NULL
);

CREATE TABLE `transactions` (
  `indexId` bigint UNSIGNED NOT NULL,
  `transactionId` binary(64) NOT NULL,
  `timestamp` bigint UNSIGNED NOT NULL,
  `source` binary(16) NOT NULL,
  `dest` binary(16) NOT NULL,
  `currencyId` binary(16) NOT NULL,
  `amount` bigint UNSIGNED NOT NULL,
  `previous` binary(64) NOT NULL,
  `publicKey` binary(64) NOT NULL,
  `adminSignature` binary(64) NOT NULL
);

ALTER TABLE `balance`
  ADD UNIQUE KEY `balance` (`address`,`currencyId`);

ALTER TABLE `currency`
  ADD UNIQUE KEY `currencyId` (`currencyId`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `symbol` (`symbol`);

ALTER TABLE `transactions`
  ADD UNIQUE KEY `indexId` (`indexId`),
  ADD UNIQUE KEY `transactionId` (`transactionId`);
COMMIT;
