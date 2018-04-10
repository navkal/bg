<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  if ( count( $_REQUEST ) )
  {
    // Get attributes
    // $sLocation = quote( $_POST['loc_new'] );
    // $sOldLocation = quote( $_POST['loc_old'] );
    // $sDescription = quote( $_POST['loc_descr'] );

    // Format command
    // $command = quote( getenv( 'PYTHON' ) ) . ' ../database/addLocation.py 2>&1 -b ' . $_SESSION['panelSpy']['user']['username']
      // . ' -l ' . $sLocation
      // . ' -o ' . $sOldLocation
      // . ' -d ' . $sDescription
      // . $g_sContext;



    $t0 = microtime( true );

    $command = quote( getenv( "PYTHON" ) ) . " bg.py -t TBD";
    error_log( "===> command=" . $command );
    exec( $command, $output, $status );
    error_log( "===> output=" . print_r( $output, true ) );

    $tBacnetRsp = json_decode( $output[ count( $output ) - 1 ] );

    $tGatewayRsp =
      [
        'elapsed_time' => round( 1000 * ( microtime( true ) - $t0 ) ) . ' ms',
        'bacnet_response' => $tBacnetRsp
      ];

    $sJson = json_encode( $tGatewayRsp );

    $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  }
  else
  {
    $sEcho = json_encode( 'BACnet Gateway request error' );
  }

  echo $sEcho;


  ///////////////////////////////////////////////////


  function quote( $s, $bTrim = true )
  {
    // Optionally trim the string
    if ( $bTrim )
    {
      $s = trim( $s );
    }

    // If string is not already quoted...
    if ( empty( $s ) || ! ( ( $s[0] == '"' ) && ( substr( $s, -1 ) == '"' ) ) )
    {
      // Replace all double quotes with single quotes
      $s = str_replace( '"', "'", $s );

      // Enclose string in quotes
      $s = '"' . $s . '"';
    }

    return $s;
  }

?>
