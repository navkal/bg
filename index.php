<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.

  require_once $_SERVER["DOCUMENT_ROOT"] . "/../common/util.php";

  // Track client IP addresses
  include $_SERVER['DOCUMENT_ROOT'] . '/clients/clients.php';

  // Determine whether to service bulk or single request
  require_once $_SERVER["DOCUMENT_ROOT"] . ( isset( $_REQUEST['bulk'] ) ? '/gb.php' : '/bg.php' );
?>
