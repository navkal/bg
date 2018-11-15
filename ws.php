<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $sKey = isset( $_REQUEST['key'] ) ? $_REQUEST['key'] : null;
  echo json_encode( $sKey );
?>
