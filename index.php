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
  else
  {
    // Load list of facilities
    getFacilities();

    if ( isset( $_REQUEST['facilities'] ) )
    {
      // Facilities map
      $sScriptName = 'fm';
    }
    else if ( findWeatherStationUrl() )
    {
      // Weather station
      $sScriptName = 'ws';
    }
    else
    {
      // BACnet Gateway
      $sScriptName = 'bg';
    }
  }

  // Service the request with the appropriate script
  require_once $_SERVER["DOCUMENT_ROOT"] . '/' . $sScriptName . '.php';


  /////////////////

  function getFacilities()
  {
    global $g_aFacilities;
    $g_aFacilities = [];

    // Open CSV file containing list of facilities
    $file = fopen( 'facilities.csv', 'r' );

    // Skip header line
    fgetcsv( $file );

    // Iterate over lines of file
    while ( ( $line = fgetcsv( $file ) ) !== FALSE )
    {
      // If line is not empty or commented out...
      if ( ( count( $line ) > 0 ) && ( trim( $line[0] ) != '' ) && ( substr( trim( $line[0] ), 0, 1 ) != '#' ) )
      {
        // Get facility name and type from line
        $sFacility = trim( $line[0] );
        $sFacilityType = trim( $line[1] );
        $sAddress = trim( $line[2] );
        $sUrl = trim( $line[3] );

        // Insert into facility map
        $g_aFacilities[$sFacility] = [ 'facility_type' => $sFacilityType, 'address' => $sAddress, 'url' => $sUrl ];
      }
      else error_log( '======> skipping <' . print_r( $line, true ) . '>' );
    }

    fclose($file);
  }

  function findWeatherStationUrl()
  {
    global $g_aFacilities;
    global $g_sWeatherStationUrl;

    $g_sWeatherStationUrl =
      isset( $_REQUEST['facility'] ) && isset( $g_aFacilities[$_REQUEST['facility']] ) && ( $g_aFacilities[$_REQUEST['facility']]['facility_type'] == 'weatherStation' )
      ?
        $g_aFacilities[$_REQUEST['facility']]['url']
      :
        ''
      ;

    return $g_sWeatherStationUrl;
  }
?>
