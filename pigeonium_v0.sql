START TRANSACTION;

CREATE DATABASE IF NOT EXISTS `pigeonium_v0`;
USE `pigeonium_v0`;

CREATE TABLE `balance` (
  `address` BINARY(16) NOT NULL,
  `currencyId` BINARY(16) NOT NULL,
  `amount` BIGINT UNSIGNED NOT NULL
);

CREATE TABLE `currency` (
  `currencyId` BINARY(16) NOT NULL,
  `name` varchar(32) NOT NULL,
  `symbol` varchar(8) NOT NULL,
  `inputData` mediumblob NOT NULL,
  `issuer` BINARY(16) NOT NULL,
  `supply` BIGINT UNSIGNED NOT NULL,
  `issuerSignature` BINARY(64) NOT NULL,
  `publicKey` BINARY(64) NOT NULL
);

CREATE TABLE `transactions` (
  `indexId` BIGINT UNSIGNED NOT NULL,
  `transactionId` BINARY(64) NOT NULL,
  `timestamp` BIGINT UNSIGNED NOT NULL,
  `source` BINARY(16) NOT NULL,
  `dest` BINARY(16) NOT NULL,
  `currencyId` BINARY(16) NOT NULL,
  `amount` BIGINT UNSIGNED NOT NULL,
  `networkId` BIGINT UNSIGNED NOT NULL,
  `publicKey` BINARY(64) NOT NULL,
  `adminSignature` BINARY(64) NOT NULL
);

CREATE TABLE liquidity_pools (
  `pairCurrency` BINARY(16) PRIMARY KEY,
  `reserveBaseCurrency` BIGINT UNSIGNED,
  `reservePairCurrency` BIGINT UNSIGNED,
  `swapFee` INT DEFAULT 3 -- 0.3%
);

CREATE TABLE swap_history (
  `swapId` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `pairCurrency` BINARY(16),
  `swapType` VARCHAR(4),
  `inputAmount` BIGINT UNSIGNED,
  `outputAmount` BIGINT UNSIGNED,
  `timestamp` BIGINT UNSIGNED
);

DELIMITER //

CREATE PROCEDURE swap_currency(
  IN p_swap_type VARCHAR(4),
  IN p_pairCurrency BINARY(16),
  IN p_input_amount DECIMAL(25,0),
  OUT p_output_amount DECIMAL(25,0)
)
BEGIN
  DECLARE v_reserve_in DECIMAL(25,0);
  DECLARE v_reserve_out DECIMAL(25,0);
  DECLARE swap_timestamp BIGINT UNSIGNED;
  DECLARE v_fee INT;

  SELECT swapFee INTO v_fee FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;
  
  SET swap_timestamp = UNIX_TIMESTAMP();

  IF p_swap_type = "buy" THEN
    SELECT reserveBaseCurrency, reservePairCurrency INTO v_reserve_in, v_reserve_out
    FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;

    SET p_output_amount = FLOOR((v_reserve_out * (p_input_amount * (1000 - v_fee)) / 1000) / (v_reserve_in + (p_input_amount * (1000 - v_fee)) / 1000));

    UPDATE liquidity_pools SET 
      reserveBaseCurrency = reserveBaseCurrency + p_input_amount, 
      reservePairCurrency = reservePairCurrency - p_output_amount 
    WHERE pairCurrency = p_pairCurrency;

  ELSEIF p_swap_type = "sell" THEN
    SELECT reservePairCurrency, reserveBaseCurrency INTO v_reserve_in, v_reserve_out
    FROM liquidity_pools WHERE pairCurrency = p_pairCurrency;

    SET p_output_amount = FLOOR((v_reserve_out * (p_input_amount * (1000 - v_fee)) / 1000) / (v_reserve_in + (p_input_amount * (1000 - v_fee)) / 1000));

    UPDATE liquidity_pools SET 
      reservePairCurrency = reservePairCurrency + p_input_amount, 
      reserveBaseCurrency = reserveBaseCurrency - p_output_amount 
    WHERE pairCurrency = p_pairCurrency;
  ELSE
    SET p_output_amount = 0;
  END IF;


  INSERT INTO swap_history (pairCurrency, swapType, inputAmount, outputAmount, timestamp)
    VALUES (p_pairCurrency, p_swap_type, p_input_amount, p_output_amount, swap_timestamp);
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
