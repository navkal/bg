<?php
  // Copyright 2018 Building Energy Gateway.  All rights reserved.

  $t0 = microtime( true );

  $sMessage = '';
  $sInstance = '';
  $g_aProperty = [];

  if ( isset( $_REQUEST['instance'] ) )
  {
    $sInstance = $_REQUEST['instance'];

    $bLive = isset( $_REQUEST['live'] );

    if ( ! $bLive)
    {
      // Try to retrieve from cache

      // Format command
      $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/read_cache.py'
        . ' -a ' . $_REQUEST['facility']
        . ' -t ' . 'weatherData'
        . ' -i ' . $_REQUEST['instance']
        . ' -p ' . 'presentValue';

      // Execute command
      error_log( "==> command=" . $command );
      exec( $command, $output, $status );
      error_log( "==> output=" . print_r( $output, true ) );

      // Extract cache response
      $tCacheRsp = json_decode( $output[ count( $output ) - 1 ] );

      if ( $tCacheRsp->success )
      {
        // Extract data from cache response
        $tData = $tCacheRsp->data;
        $g_aProperty = [ 'value' => $tData->presentValue, 'units' => $tData->units, 'timestamp' => $tData->timestamp ];
      }
      else
      {
        // Set flag to retry as a live request
        $bLive = true;
      }
    }

    if ( $bLive )
    {
      // Issue request to web service
      $curl = curl_init();
      curl_setopt( $curl, CURLOPT_RETURNTRANSFER, true );
      curl_setopt( $curl, CURLOPT_URL, $g_sWeatherStationUrl );
      $aRsp = json_decode( json_encode( json_decode( curl_exec( $curl ) ) ), true );

      // Traverse response to find requested property
      extractProperty( $sInstance, $aRsp );
    }

    if ( empty( $g_aProperty ) )
    {
      $sMessage = "Instance '" . $sInstance . "' not found";
    }
  }
  else
  {
    $sMessage = "Parameter 'instance' is missing";
  }

  // Build response structure

  $tInstanceRsp =
  [
    'message' => $sMessage,
    'success' => ( $sMessage == '' )
  ];

  if ( $tInstanceRsp['success'] )
  {
    // Load data into response
    $tInstanceRsp['data'] =
    [
      'message' => '',
      'success' => true,
      'instance' => $sInstance,
      'property' => 'presentValue',
      'presentValue' => $g_aProperty['value'],
      'units' => $g_aProperty['units']
    ];

    if ( $bLive )
    {
      // Save live result in cache
      writeCache( $tInstanceRsp['data'] );
    }
    else
    {
      // Add cache timestamp to response
      $tInstanceRsp['data']['timestamp'] = $g_aProperty['timestamp'];
    }
  }

  $tGatewayRsp =
  [
    'instance_response' => $tInstanceRsp,
    'service_time' => round( 1000 * ( microtime( true ) - $t0 ) ) . ' ms'
  ];

  // Return JSON
  $sJson = json_encode( $tGatewayRsp, JSON_PRETTY_PRINT );
  $sEcho = isset( $_GET['callback'] ) ? $_GET['callback'] . '(' . $sJson . ');' : $sJson;
  header( 'Content-Type: application/json' );
  echo $sEcho;



  ////////////////////////////////////////////

  function extractProperty( $sPropName, $aRsp )
  {
    global $g_aProperty;

    foreach ( $aRsp as $sKey => $val )
    {
      if ( is_array( $val ) )
      {
        extractProperty( $sPropName, $val );
      }
      else
      {
        if ( $sPropName == $sKey )
        {
          $g_aProperty = [ 'value' => $val, 'units' => ( $val === null ) ? '' : makeUnits( $sPropName ) ];
        }
      }

      if ( ! empty( $g_aProperty  ) )
      {
        break;
      }
    }
  }

  function makeUnits( $sPropName )
  {
    $sDegrees = 'deg';
    $sDegreesF = 'deg F';
    $sPercent = 'pct';
    $sPerHour = '/hr';
    $sInches = 'in';
    $sMph = 'mph';
    $sNoUnits = '';

    $tUnitsMap =
    [
      // 'observation'
      'key' => $sNoUnits,
      'stationId' => $sNoUnits,
      'providerId' => $sNoUnits,
      'observationTimeLocalStr' => $sNoUnits,
      'observationTimeUtcStr' => $sNoUnits,
      'iconCode' => $sNoUnits,
      'altimeter' => '',
      'altimeterRate' => '',
      'dewPoint' => $sDegreesF,
      'dewPointRate' => $sDegreesF . $sPerHour,
      'heatIndex' => $sDegreesF,
      'humidity' => $sPercent,
      'humidityRate' => $sPercent . $sPerHour,
      'pressureSeaLevel' => $sInches,
      'pressureSeaLevelRate' => $sInches . $sPerHour,
      'rainDaily' => $sInches,
      'rainRate' => $sInches . $sPerHour,
      'rainMonthly' => $sInches,
      'rainYearly' => $sInches,
      'snowDaily' => $sInches,
      'snowRate' => $sInches . $sPerHour,
      'snowMonthly' => $sInches,
      'snowYearly' => $sInches,
      'temperature' => $sDegreesF,
      'temperatureRate' => $sDegreesF . $sPerHour,
      'visibility' => '',
      'visibilityRate' => '',
      'windChill' => $sDegreesF,
      'windSpeed' => $sMph,
      'windDirection' => $sDegrees,
      'windSpeedAvg' => $sMph,
      'windDirectionAvg' => $sDegrees,
      'windGustHourly' => $sMph,
      'windGustTimeLocalHourlyStr' => '',
      'windGustTimeUtcHourlyStr' => '',
      'windGustDirectionHourly' => '',
      'windGustDaily' => '',
      'windGustTimeLocalDailyStr' => '',
      'windGustTimeUtcDailyStr' => '',
      'windGustDirectionDaily' => '',
      'observationTimeAdjustedLocalStr' => '',
      'feelsLike' => $sDegreesF,
      // 'highlow'
      'humidityHigh' => '',
      'humidityHighLocalStr' => '',
      'humidityHighUtcStr' => '',
      'humidityLow' => '',
      'humidityLowLocalStr' => '',
      'humidityLowUtcStr' => '',
      'pressureSeaLevelHigh' => '',
      'pressureSeaLevelHighLocalStr' => '',
      'pressureSeaLevelHighUtcStr' => '',
      'pressureSeaLevelLow' => '',
      'pressureSeaLevelLowLocalStr' => '',
      'pressureSeaLevelLowUtcStr' => '',
      'rainRateMax' => '',
      'rainRateMaxLocalStr' => '',
      'rainRateMaxUtcStr' => '',
      'temperatureHigh' => '',
      'temperatureHighLocalStr' => '',
      'temperatureHighUtcStr' => '',
      'temperatureLow' => '',
      'temperatureLowLocalStr' => '',
      'temperatureLowUtcStr' => '',
      // 'station'
      'StationId' => '',
      'ProviderId' => '',
      'ProviderName' => '',
      'StationName' => '',
      'Latitude' => '',
      'Longitude' => '',
      'ElevationAboveSeaLevel' => ''
    ];

    $sUnits = isset( $tUnitsMap[$sPropName] ) ? $tUnitsMap[$sPropName] : '';

    return $sUnits;
  }

  function writeCache( $aData )
  {
    global $g_sWeatherStationUrl;

    // Format command
    $command = SUDO . quote( getenv( "PYTHON" ) ) . ' cache/write_cache.py'
      . ' -a ' . $_REQUEST['facility']
      . ' -t ' . 'weatherData'
      . ' -i ' . $_REQUEST['instance']
      . ' -p ' . 'presentValue'
      . ' -v ' . quote( $aData['presentValue'] )
      . ' -u ' . quote( $aData['units'] );

    // Execute command
    error_log( "==> command=" . $command );
    exec( $command, $output, $status );
    error_log( "==> output=" . print_r( $output, true ) );
  }

?>
