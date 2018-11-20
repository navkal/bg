<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  require_once $_SERVER["DOCUMENT_ROOT"] . "/../common/util.php";

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  // Track client IP addresses
  include $_SERVER['DOCUMENT_ROOT'] . '/clients/clients.php';

  // Determine how to service the request
  $sScriptName = '';
  if ( isset( $_REQUEST['bulk'] ) )
  {
    // Get bulk
    $sScriptName = 'gb';
  }
  else if ( requestingWeatherStation() )
  {
    // Weather station
    $sScriptName = 'ws';
  }
  else
  {
    // BACnet Gateway
    $sScriptName = 'bg';
  }

  // Service the request with the appropriate script
  require_once $_SERVER["DOCUMENT_ROOT"] . '/' . $sScriptName . '.php';


  /////////////////

  function requestingWeatherStation()
  {
    global $g_sStationUrl;
    $g_sStationUrl = '';

    if ( isset( $_REQUEST['facility'] ) )
    {
      // Open CSV file containing list of weather stations
      $file = fopen( 'facilities.csv', 'r' );
      fgetcsv( $file );

      // Search CSV file for matching facility name
      while ( ( ( $line = fgetcsv( $file ) ) !== FALSE ) && ! $g_sStationUrl )
      {
        if ( $_REQUEST['facility'] == $line[0] )
        {
          // Facility name found; save URL
          $g_sStationUrl = $line[3];
        }
      }

      fclose($file);
    }

    return $g_sStationUrl;
  }

?>
