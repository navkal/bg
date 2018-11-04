<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  if ( $_SERVER['REMOTE_ADDR'] != '127.0.0.1' )
  {
    $aOptions =
    [
      'REMOTE_ADDR',
      'HTTP_X_FORWARDED_FOR',
      'HTTP_REFERER',
      'REQUEST_TIME'
    ];

    $sArgs = '';

    foreach( $aOptions as $sOption )
    {
      $sArgs .= makeArg( $sOption );
    }

    // Format command
    $command = SUDO . quote( getenv( 'PYTHON' ) ) . ' clients/clients.py 2>&1 ' . $sArgs;

    // Execute command
    error_log( '==> command=' . $command );
    exec( $command, $output, $status );
    error_log( '==> output=' . print_r( $output, true ) );
  }

  /////////////////////////

  function makeArg( $sOption )
  {
    $sArg = quote( ( isset( $_SERVER[$sOption] ) ) ? $_SERVER[$sOption] : '' );
    return ' --' . $sOption . ' ' . quote( ( isset( $_SERVER[$sOption] ) ) ? $_SERVER[$sOption] : '' );
  }
?>
