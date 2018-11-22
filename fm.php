<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $aFacilityMap = [];

  foreach ( $g_aFacilities as $sFacType => $aFacsOfType )
  {
    $aFacilityMap[$sFacType] = [];
    foreach ( $aFacsOfType as $sFacName => $aFac )
    {
      array_push( $aFacilityMap[$sFacType], $sFacName );
    }
  }

  // Echo result
  echo json_encode( $aFacilityMap );
?>
