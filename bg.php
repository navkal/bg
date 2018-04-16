<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  $bGotAllArgs = isset(
    $_REQUEST['address'],
    $_REQUEST['type'],
    $_REQUEST['instance'],
    $_REQUEST['property']
  );

  if ( $bGotAllArgs )
  {
    $t0 = microtime( true );

    // Format command
    $command = quote( getenv( "PYTHON" ) ) . ' bg.py'
      . ' -a ' . $_REQUEST['address']
      . ' -t ' . $_REQUEST['type']
      . ' -i ' . $_REQUEST['instance']
      . ' -p ' . $_REQUEST['property'];

    error_log( "===> command=" . $command );
    exec( $command, $output, $status );
    error_log( "===> output=" . print_r( $output, true ) );

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
        'service_time' => round( 1000 * ( microtime( true ) - $t0 ) ) . ' ms',
        'bacnet_response' => $tBacnetRsp
      ];

    $sJson = json_encode( $tGatewayRsp );

    $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  }
  else
  {
    $sEcho = json_encode( 'BACnet Gateway request arguments missing' );
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
