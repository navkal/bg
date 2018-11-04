<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  error_log( '==> request=' . print_r( $_REQUEST, true ) );

  // Format command
  $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/get_bulk.py -b ' . quote( str_replace( '"', "'", $_REQUEST['bulk'] ) );

  // Execute command
  error_log( "==> command=" . $command );
  exec( $command, $output, $status );
  error_log( "==> output=" . print_r( $output, true ) );

  // Echo result
  echo $output[ count( $output ) - 1 ];
?>
