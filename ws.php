<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $t0 = microtime( true );

  $sMessage = '';
  $sInstance = '';
  $g_aProperty = [];

  if ( isset( $_REQUEST['instance'] ) )
  {

    $sInstance = $_REQUEST['instance'];

    // Issue request to web service
    $curl = curl_init();
    curl_setopt( $curl, CURLOPT_RETURNTRANSFER, true );
    curl_setopt( $curl, CURLOPT_URL, $g_sStationUrl );
    $aRsp = json_decode( json_encode( json_decode( curl_exec( $curl ) ) ), true );

    // Traverse response to find requested property
    extractProperty( $sInstance, $aRsp );

    if ( empty( $g_aProperty ) )
    {
      $sMessage = "Instance '" . $sInstance . "' not found";
    }
  }
  else
  {
    $sMessage = "Parameter 'instance' is missing";
  }

  // Build response structure

  $tInstanceRsp =
  [
    'message' => $sMessage,
    'success' => ( $sMessage == '' )
  ];

  if ( $tInstanceRsp['success'] )
  {
    // Load data into response
    $tInstanceRsp['data'] =
    [
      'message' => '',
      'success' => true,
      'instance' => $sInstance,
      'property' => 'presentValue',
      'presentValue' => $g_aProperty['value'],
      'units' => $g_aProperty['units']
    ];

    // Save result in cache
    writeCache( $tInstanceRsp['data'] );
  }

  $tGatewayRsp =
  [
    'instance_response' => $tInstanceRsp,
    'service_time' => round( 1000 * ( microtime( true ) - $t0 ) ) . ' ms'
  ];

  // Return JSON
  $sJson = json_encode( $tGatewayRsp, JSON_PRETTY_PRINT );
  $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  header( 'Content-Type: application/json' );
  echo $sEcho;



  ////////////////////////////////////////////

  function extractProperty( $sPropName, $aRsp )
  {
    global $g_aProperty;

    foreach ( $aRsp as $sKey => $val )
    {
      error_log( '===> trying ' . $sKey );
      if ( is_array( $val ) )
      {
        extractProperty( $sPropName, $val );
      }
      else
      {
        if ( $sPropName == $sKey )
        {
          $g_aProperty = [ 'value' => $val, 'units' => makeUnits( $sPropName ) ];
          error_log( '========> DONE' );
        }
      }

      if ( ! empty( $g_aProperty  ) )
      {
        break;
      }
    }
  }

  function makeUnits( $sPropName )
  {
    $tUnitsMap =
    [
      'temperature' => 'deg F',
      'humidity' => '%'
    ];

    $sUnits = isset( $tUnitsMap[$sPropName] ) ? $tUnitsMap[$sPropName] : '';

    return $sUnits;
  }

  function writeCache( $aData )
  {
    // Format command, filling in unused parameters with defaults applicable to BACnet values
    $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/write_cache.py'
      . ' -a ' . $_REQUEST['facility']
      . ' -t ' . 'analogInput'
      . ' -i ' . $_REQUEST['instance']
      . ' -p ' . 'presentValue'
      . ' -v ' . quote( $aData['presentValue'] )
      . ' -u ' . quote( $aData['units'] );

    // Execute command
    error_log( "==> command=" . $command );
    exec( $command, $output, $status );
    error_log( "==> output=" . print_r( $output, true ) );
  }

?>
