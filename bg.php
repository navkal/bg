<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.
  require_once $_SERVER["DOCUMENT_ROOT"] . "/../common/util.php";

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  // Map facility name to IP address
  if ( isset( $_REQUEST['facility'] ) )
  {
    // Make sure we don't have an address argument
    unset( $_REQUEST['address'] );

    // Open CSV file containing mappings from facility names to IP addresses
    $file = fopen( 'agents.csv', 'r' );

    // Read the prefix
    $aLine = fgetcsv( $file );
    $sPrefix = $aLine[0];

    // Traverse lines of the file until match is found
    $bFound = false;
    while( ! $bFound && ! feof( $file ) )
    {
      // Get next line
      $aLine = fgetcsv( $file );

      // If there is a match, set parameter
      if ( $aLine[0] == $_REQUEST['facility'] )
      {
        $bFound = true;
        $_REQUEST['address'] = long2ip( hexdec( $sPrefix . $aLine[1] ) );
      }
    }

    if ( ! $bFound )
    {
      $sMessage = 'Facility ' . "'" . $_REQUEST['facility'] . "'" . ' not found.';
    }

    fclose( $file );
  }

  // Set default type
  if ( ! isset( $_REQUEST['type'] ) )
  {
    $_REQUEST['type'] = 'analogInput';
  }

  // Set default property
  if ( ! isset( $_REQUEST['property'] ) )
  {
    $_REQUEST['property'] = 'presentValue';
  }

  $bGotAllArgs = isset(
    $_REQUEST['address'],
    $_REQUEST['type'],
    $_REQUEST['instance'],
    $_REQUEST['property']
  );

  if ( $bGotAllArgs )
  {
    $t0 = microtime( true );

    // Determine whether to forego cached data
    $bLive = isset( $_REQUEST['live'] ) || ( $_REQUEST['type'] != 'analogInput' ) || ( $_REQUEST['property'] != 'presentValue' );

    if ( ! $bLive)
    {
      // Try to retrieve from Building Monitor cache

      // Format command
      $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/read_cache.py'
        . ' -f ' . $_REQUEST['facility']
        . ' -i ' . $_REQUEST['instance'];

      // Execute command
      error_log( "===> command=" . $command );
      exec( $command, $output, $status );
      error_log( "===> output=" . print_r( $output, true ) );

      // Determine whether to retry with live request
      $tCacheRsp = json_decode( $output[ count( $output ) - 1 ] );
      $bLive = ! $tCacheRsp->success;
    }

    if ( $bLive )
    {
      // Did not (or could not) retrieve value from cache.  Get live value.

      // Format command
      $command = SUDO . quote( getenv( "PYTHON" ) ) . ' live/bg.py'
        . ' -a ' . $_REQUEST['address']
        . ' -t ' . $_REQUEST['type']
        . ' -i ' . $_REQUEST['instance']
        . ' -p ' . $_REQUEST['property'];

      // Execute command
      error_log( "===> command=" . $command );
      exec( $command, $output, $status );
      error_log( "===> output=" . print_r( $output, true ) );

      $tLiveRsp = json_decode( $output[ count( $output ) - 1 ] );
      if ( $tLiveRsp->success && $tLiveRsp->data->success )
      {
        // Save result in cache
        writeCache( (array) $tLiveRsp->data );
      }
    }

    $iRspOffset = count( $output ) - 1;
    if ( $iRspOffset >= 0 )
    {
      $tBacnetRsp = json_decode( $output[ $iRspOffset ] );
    }
    else
    {
      $tBacnetRsp = [ 'status' => $status ];
    }


    $tGatewayRsp =
    [
      'bacnet_response' => $tBacnetRsp,
      'service_time' => round( 1000 * ( microtime( true ) - $t0 ) ) . ' ms'
    ];

    $sJson = json_encode( $tGatewayRsp );

    $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  }
  else
  {
    if ( ! isset( $sMessage ) )
    {
      $sMessage = 'BACnet Gateway request arguments missing';
    }

    $sEcho = json_encode( $sMessage );
  }

  echo $sEcho;


  ////////////////////////////////////////////

  function writeCache( $aData )
  {
    error_log( '==> ===> WRITE CACHE: request=' . print_r( $_REQUEST, true ) );
    error_log( '==> ===> WRITE CACHE: data=' . print_r( $aData, true ) );

    // Format command
    $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/write_cache.py'
      . ' -a ' . $_REQUEST['address']
      . ' -t ' . $_REQUEST['type']
      . ' -i ' . $_REQUEST['instance']
      . ' -p ' . $_REQUEST['property']
      . ' -v ' . $aData[$_REQUEST['property']]
      . ' -u ' . $aData['units'];

    // Execute command
    error_log( "===> command=" . $command );
    exec( $command, $output, $status );
    error_log( "===> output=" . print_r( $output, true ) );
  }
?>
