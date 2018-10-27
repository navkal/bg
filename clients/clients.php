<?php
  // Copyright 2018 BACnet Gateway.  All rights reserved.

  $sIp = $_SERVER['REMOTE_ADDR'];
  $sFwdIp = isset( $_SERVER['HTTP_X_FORWARDED_FOR'] ) ? $_SERVER['HTTP_X_FORWARDED_FOR'] : '';

  // Format command
  $command = quote( getenv( 'PYTHON' ) ) . ' clients/clients.py 2>&1 -i ' . quote( $sIp ) . ' -f ' . quote( $sFwdIp );

  // Execute command
  error_log( '==> command=' . $command );
  exec( $command, $output, $status );
  error_log( '==> output=' . print_r( $output, true ) );
?>
