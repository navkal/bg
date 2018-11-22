<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $aFacilities = [];

  foreach ( $g_aFacilities as $sName => $aProps )
  {
    $aFacilities[$sName] = [ 'facility_type' => $g_aFacilities[$sName]['facility_type'] ];
  }

  // Echo result
  echo json_encode( $aFacilities );
?>
