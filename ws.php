<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  define( 'NO_PROPERTY', 'NO_PROPERTY' );

  // Table of weather stations
  $aStations =
  [
    'ahs' =>
    [
      'label' => 'Andover High School',
      'url' => 'https://owc.enterprise.earthnetworks.com/Data/GetData.ashx?dt=o&pi=3&si=ANSHS&locstr=42.65998,-71.15531&units=english&verbose=true'
    ]
  ];

  // Get request arguments
  $sStation = $_REQUEST['station'];
  $sProperty = isset( $_REQUEST['property'] ) ? $_REQUEST['property'] : '';

  $sMessage = '';
  $sLabel = '';
  $property = NO_PROPERTY;

  // Look for requested weather station in table
  if ( isset( $aStations[$sStation] ) )
  {
    // Set label for requested weather station
    $sLabel = $aStations[$sStation]['label'];

    // Issue request to web service
    $curl = curl_init();
    curl_setopt( $curl, CURLOPT_RETURNTRANSFER, true );
    curl_setopt( $curl, CURLOPT_URL, $aStations[$sStation]['url'] );
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
  }
  else
  {
    // Requested weather station not found
    $property = '';
    $sMessage = "Station '" . $sStation . "' not found";
  }

  // Load results into structure
  $aResult =
  [
    'success' => ( $sMessage == '' ),
    'message' => $sMessage,
    'station' => $sStation,
    'label' => $sLabel,
    'requestedProperty' => $sProperty,
    $sProperty => $property
  ];

  // Return JSON
  $sEcho = json_encode( $aResult );
  echo $sEcho;
