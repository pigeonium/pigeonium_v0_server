START TRANSACTION;

CREATE DATABASE IF NOT EXISTS `pigeonium_v0`;
USE `pigeonium_v0`;

CREATE TABLE `balance` (
  `address` binary(16) NOT NULL,
  `currencyId` binary(16) NOT NULL,
  `amount` bigint UNSIGNED NOT NULL
);

CREATE TABLE `currency` (
  `currencyId` binary(16) NOT NULL,
  `name` varchar(32) NOT NULL,
  `symbol` varchar(8) NOT NULL,
  `inputData` mediumblob NOT NULL,
  `issuer` binary(16) NOT NULL,
  `supply` bigint UNSIGNED NOT NULL,
  `issuerSignature` binary(64) NOT NULL,
  `publicKey` binary(64) NOT NULL
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

CREATE TABLE liquidity_pools (
  `pairCurrency` BINARY(16) PRIMARY KEY,
  `reserve_BaseCurrency` bigint UNSIGNED,
  `reserve_PairCurrency` bigint UNSIGNED,
  `swap_fee` INT DEFAULT 3 -- 0.3%
);

DELIMITER //

CREATE PROCEDURE swap_currency(
  IN p_buy_sell VARCHAR(4),
  IN p_pairCurrency BINARY(16),
  IN p_input_amount BIGINT UNSIGNED,
  OUT p_output_amount BIGINT UNSIGNED
)
BEGIN
  DECLARE v_reserve_in BIGINT UNSIGNED;
  DECLARE v_reserve_out BIGINT UNSIGNED;
  DECLARE v_fee INT;

  SELECT swap_fee INTO v_fee FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;

  IF p_buy_sell = "buy" THEN
    SELECT reserve_BaseCurrency, reserve_PairCurrency INTO v_reserve_in, v_reserve_out
    FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;

    SET p_output_amount = FLOOR((v_reserve_out * (p_input_amount * (1000 - v_fee)) / 1000) / (v_reserve_in + (p_input_amount * (1000 - v_fee)) / 1000));

    UPDATE liquidity_pools SET 
      reserve_BaseCurrency = reserve_BaseCurrency + p_input_amount, 
      reserve_PairCurrency = reserve_PairCurrency - p_output_amount 
    WHERE pairCurrency = p_pairCurrency;

  ELSEIF p_buy_sell = "sell" THEN
    SELECT reserve_PairCurrency, reserve_BaseCurrency INTO v_reserve_in, v_reserve_out
    FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;

    SET p_output_amount = FLOOR((v_reserve_out * (p_input_amount * (1000 - v_fee)) / 1000) / (v_reserve_in + (p_input_amount * (1000 - v_fee)) / 1000));

    UPDATE liquidity_pools SET 
      reserve_PairCurrency = reserve_PairCurrency + p_input_amount, 
      reserve_BaseCurrency = reserve_BaseCurrency - p_output_amount 
    WHERE pairCurrency = p_pairCurrency;
  ELSE
    SET p_output_amount = 0;
  END IF;
END //

DELIMITER ;

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
