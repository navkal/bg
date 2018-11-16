<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $sMessage = '';
  $sInstance = '';
  $g_aProperty = [];

  if ( isset( $_REQUEST['instance'] ) )
  {
    $t0 = microtime( true );

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

  // Load results into structure

  $tInstanceRsp =
  [
    'data' =>
    [
      'message' => '',
      'success' => true,
      'property' => $sInstance,
      $sInstance => $g_aProperty['value'],
      'units' => $g_aProperty['units']
    ],
    'message' => $sMessage,
    'success' => ( $sMessage == '' ),
  ];

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
      error_log( 'trying ' . $sKey );
      if ( is_array( $val ) )
      {
        extractProperty( $sPropName, $val );
      }
      else
      {
        if ( $sPropName == $sKey )
        {
          $g_aProperty = [ 'value' => $val, 'units' => 'foonits' ];
          error_log( '========> DONE' );
        }
      }

      if ( ! empty( $g_aProperty  ) )
      {
        break;
      }
    }
  }
?>
