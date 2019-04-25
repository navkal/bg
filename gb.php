<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  // Abbreviate property names to work around Windows 10 limitation of command line length to 8191 characters
  $aRq = json_decode( $_REQUEST['bulk'] );
  foreach ( $aRq as $sKey => $tVal )
  {
    $tVal->f = $tVal->facility;
    unset( $tVal->facility );
    $tVal->i = $tVal->instance;
    unset( $tVal->instance );
  }
  $_REQUEST['bulk'] = json_encode( $aRq );

  // Format command
  $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/get_bulk.py -b ' . quote( str_replace( '"', "'", $_REQUEST['bulk'] ) );

  // Execute command
  error_log( "==> command=" . $command );
  exec( $command, $output, $status );
  error_log( "==> output=" . print_r( $output, true ) );

  // Echo result
  echo $output[ count( $output ) - 1 ];
?>
