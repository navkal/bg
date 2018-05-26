<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  // Map NAE name to IP address
  if ( isset( $_REQUEST['nae'] ) )
  {
    // Make sure we don't have an address argument
    unset( $_REQUEST['address'] );

    // Open CSV file containing mappings from NAE names to IP addresses
    $file = fopen( "nae_map.csv","r" );

    // Traverse lines of the file until match is found
    $bFound = false;
    while( ! $bFound && ! feof( $file ) )
    {
      // Get next line
      $aLine = fgetcsv( $file );

      // If there is a match, save mapping
      if ( $aLine[0] == $_REQUEST['nae'] )
      {
        $bFound = true;
        $_REQUEST['address'] = $aLine[1];
      }
    }

    if ( ! $bFound )
    {
      $sMessage = 'NAE ' . "'" . $_REQUEST['nae'] . "'" . ' not found.';
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
