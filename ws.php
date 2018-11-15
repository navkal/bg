<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $sProperty = isset( $_REQUEST['property'] ) ? $_REQUEST['property'] : 'temperature';

  $sKey = 'temperature';  // <-- fake

  // Issue request to web service
  $curl = curl_init();
  curl_setopt( $curl, CURLOPT_RETURNTRANSFER, true );
  curl_setopt( $curl, CURLOPT_URL, "https://owc.enterprise.earthnetworks.com/Data/GetData.ashx?dt=o&pi=3&si=ANSHS&locstr=42.65998,-71.15531&units=english&verbose=true" );
  $aResult = json_decode( json_encode( json_decode( curl_exec( $curl ) ) ), true );

  // Extract requested item
  $sTemp = $aResult['observation'][$sKey];

  // Return JSON
  $sEcho = json_encode( $sTemp );
  echo $sEcho;
