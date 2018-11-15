<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  require_once $_SERVER["DOCUMENT_ROOT"] . "/../common/util.php";

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  // Track client IP addresses
  include $_SERVER['DOCUMENT_ROOT'] . '/clients/clients.php';

  // Determine how to service the request
  $sScriptName = '';
  if ( isset( $_REQUEST['station'] ) )
  {
    // Weather station
    $sScriptName = 'ws';
  }
  else if ( isset( $_REQUEST['bulk'] ) )
  {
    // Get bulk
    $sScriptName = 'gb';
  }
  else
  {
    // BACnet Gateway
    $sScriptName = 'bg';
  }

  // Service the request with the appropriate script
  require_once $_SERVER["DOCUMENT_ROOT"] . '/' . $sScriptName . '.php';
?>
