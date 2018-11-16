<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  define( 'NO_PROPERTY', 'NO_PROPERTY' );

  // Get request argument
  $sProperty = isset( $_REQUEST['instance'] ) ? $_REQUEST['instance'] : '';

  $sMessage = '';
  $property = NO_PROPERTY;

  // Issue request to web service
  $curl = curl_init();
  curl_setopt( $curl, CURLOPT_RETURNTRANSFER, true );
  curl_setopt( $curl, CURLOPT_URL, $g_sStationUrl );
  $aRsp = json_decode( json_encode( json_decode( curl_exec( $curl ) ) ), true );

  // Determine result: either requested property or full response
  if ( $sProperty )
  {
    // Caller requested a property; search for it in the response

    if ( array_key_exists( $sProperty, $aRsp ) )
    {
      // Requested property found at top level of response
      $property = $aRsp[$sProperty];
    }
    else
    {
      foreach ( $aRsp as $aProps )
      {
        if ( array_key_exists( $sProperty, $aProps ) )
        {
          // Requested property found at second level of response
          $property = $aProps[$sProperty];
          break;
        }
      }
    }

    if ( $property == NO_PROPERTY )
    {
      // Requested property not found
      $property = '';
      $sMessage = "Property '" . $sProperty . "' not found";
    }
  }
  else
  {
    // Caller did not request a property; return full response
    $property = $aRsp;
  }

  // Load results into structure
  $aResult =
  [
    'success' => ( $sMessage == '' ),
    'message' => $sMessage,
    'requestedProperty' => $sProperty,
    $sProperty => $property
  ];

  // Return JSON
  $sJson = json_encode( $aResult, JSON_PRETTY_PRINT );
  $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  header( 'Content-Type: application/json' );
  echo $sEcho;
